#!/usr/bin/env python3
"""
pipeline_runner.py — NeuroAd Pipeline A Orchestrator

Runs all scoring modules sequentially on a campaign's assets folder.
Designed to be extended with MiroFish API when ready.

Usage:
    python pipeline_runner.py campaigns/nike_2026/
    python pipeline_runner.py campaigns/nike_2026/ --brand-labels "sporty" "premium" "innovative"
    python pipeline_runner.py campaigns/nike_2026/ --skip tribe  # skip slow modules
    python pipeline_runner.py campaigns/nike_2026/ --only clip   # run single module

Modules (all optional, controlled via --skip / --only):
    tribe     — TRIBE v2 neural response (~8 min/video)
    saliency  — ViNet-S/A visual attention (~22s/video)
    clip      — CLIP brand consistency (~2s/asset)
    emotion   — HSEmotion facial emotion detection (~5s/video)
    mirofish  — Social simulation (manual for now, API coming)
"""

import argparse
import gc
import json
import logging
import os
import subprocess
import time
import requests
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# MiroFish API configuration
# ---------------------------------------------------------------------------

from mirofish_client import MiroFishClient

MAX_POLL_RETRIES = 30
POLL_INTERVAL = 5  # seconds

import torch

# ---------------------------------------------------------------------------
# LLM Cache Flush Configuration
# ---------------------------------------------------------------------------

def restart_lemonade_server():
    """
    Hard reset the Lemonade server to clear VRAM.
    
    1. Kills the running server on port 8888 (aggressive double-check)
    2. Waits 10 seconds for VRAM to be physically cleared (AMD driver requirement)
    3. Starts the server with subprocess.Popen (ctx-size reduced to 128k)
    4. Waits 25 seconds for the server to be API-ready
    """
    import subprocess
    
    logger.info("Performing hard reset on Lemonade server to clear VRAM...")
    
    # 1. Aggressive double-check kill to ensure VRAM is freed
    logger.info("  [LEMONADE] Killing existing server on port 8888...")
    os.system("killall -9 lemonade-server > /dev/null 2>&1 || true")
    os.system("fuser -k -9 8888/tcp > /dev/null 2>&1 || true")
    os.system("killall -9 llama-server > /dev/null 2>&1 || true")
    os.system("fuser -k -9 /dev/kfd > /dev/null 2>&1 || true")  # Das ist der ultimative AMD ROCm Nuke
    
    # 2. Wait for VRAM to be physically cleared (AMD driver requirement)
    logger.info("[LEMONADE] Waiting 45s for Linux kernel to completely flush UMA memory...")
    time.sleep(45)
    
    # 3. Start the server in background (reduced ctx-size for OOM protection)
    logger.info("  [LEMONADE] Starting server in background...")
    subprocess.Popen(
        [
            "lemonade-server", "serve",
            "--host", "0.0.0.0",
            "--port", "8888",
            "--extra-models-dir", "/home/vincent/jarvis_os/models",
            "--ctx-size", "32768"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # 4. Wait for server to be API-ready
    logger.info("[LEMONADE] Waiting 45s for server to allocate VRAM and index models...")
    time.sleep(45)
    
    logger.info("  [LEMONADE] Server restart complete")


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# ---------------------------------------------------------------------------
# Supported file types
# ---------------------------------------------------------------------------

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALL_EXTENSIONS   = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS

# ---------------------------------------------------------------------------
# Default config
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    # Modules to run
    "modules": {
        "tribe":    {"enabled": True},
        "saliency": {"enabled": True},
        "clip":     {"enabled": True},
        "emotion":  {"enabled": True},
        "mirofish": {"enabled": True},  # API is now ready
    },

    # TRIBE v2
    "tribe": {
        "device": "auto",
        "model_id": "facebook/tribev2",
    },

    # ViNet-S/A Saliency
    "saliency": {
        "device": "auto",
        "n_frames": 32,
        "checkpoint": None,  # Auto-detected from tools/ViNet_v2/final_models/
        # Set to "vinet_a" to use Audio-Visual model instead of ViNet-S
        "model_variant": "vinet_s",
    },

    # CLIP
    "clip": {
        "device": "auto",
        "model_name": "ViT-B/32",
        "brand_labels": ["advertisement", "product", "brand"],
    },

    # HSEmotion
    "emotion": {
        "device": "auto",
        "detector": "auto",       # face detector backend
        "sample_every_n": 10,     # analyze every Nth frame (saves time)
    },

    # Composite weights
    "weights": {
        "neural_engagement":  0.25,
        "emotional_impact":   0.15,
        "visual_attention":   0.20,
        "brand_consistency":  0.15,
        "social_sentiment":   0.10,  # neutral placeholder until MiroFish
        "facial_emotion":     0.10,
        "audio_engagement":   0.05,
    },
}


# ---------------------------------------------------------------------------
# Asset collection
# ---------------------------------------------------------------------------

def collect_assets(campaign_dir: Path) -> list[Path]:
    """Collect all supported media files from campaign's assets/ folder."""
    assets_dir = campaign_dir / "assets"
    if not assets_dir.exists():
        raise FileNotFoundError(f"Assets directory not found: {assets_dir}")

    assets = sorted([
        f for f in assets_dir.iterdir()
        if f.suffix.lower() in ALL_EXTENSIONS and f.is_file()
    ])

    logger.info(f"Found {len(assets)} assets in {assets_dir}")
    for a in assets:
        logger.info(f"  {a.name} ({a.suffix})")

    return assets


# ---------------------------------------------------------------------------
# Module runners
# ---------------------------------------------------------------------------

def run_tribe(asset_path: Path, config: dict, scores_dir: Path) -> dict:
    """Run TRIBE v2 neural scoring."""
    from model_manager import SequentialTribeScorer

    cached_path = scores_dir / f"{asset_path.stem}_tribe_scores.json"
    if cached_path.exists():
        logger.info(f"  [TRIBE] Cache hit: {cached_path.name}")
        return json.loads(cached_path.read_text())

    scorer = SequentialTribeScorer(
        tribe_model_id=config["tribe"]["model_id"],
        device=config["tribe"]["device"],
    )
    result = scorer.score_asset(str(asset_path), save_preds=True)
    scorer.unload()

    cached_path.write_text(json.dumps(result, indent=2))
    return result


def run_saliency(asset_path: Path, config: dict, scores_dir: Path,
                 rois: dict | None = None) -> dict:
    """Run ViNet-S/A saliency scoring."""
    from saliency_scorer import SaliencyScorer

    cached_path = scores_dir / f"{asset_path.stem}_saliency_scores.json"
    if cached_path.exists():
        logger.info(f"  [SALIENCY] Cache hit: {cached_path.name}")
        return json.loads(cached_path.read_text())

    # Find checkpoint based on variant
    checkpoint = config["saliency"]["checkpoint"]
    if checkpoint is None:
        variant = config["saliency"]["model_variant"]
        base = Path(__file__).parent / "tools" / "ViNet_v2" / "final_models"
        if variant == "vinet_a":
            candidates = list(base.glob("ViNet_A/vinet_a_visual_dataset_models/*dhf1k*.pt"))
        else:
            candidates = list(base.glob("ViNet_S/vinet_s_visual_dataset_models/*dhf1k*.pt"))
        if candidates:
            checkpoint = str(candidates[0])
            logger.info(f"  [SALIENCY] Using checkpoint: {Path(checkpoint).name}")

    scorer = SaliencyScorer(
        checkpoint_path=checkpoint,
        device=config["saliency"]["device"],
        n_frames=config["saliency"]["n_frames"],
    )
    result = scorer.score_asset(str(asset_path), rois=rois, save_outputs=True)
    scorer.unload()

    cached_path.write_text(json.dumps(result, indent=2))
    return result


def run_clip(asset_path: Path, config: dict, scores_dir: Path) -> dict:
    """Run CLIP brand consistency scoring."""
    import clip as clip_lib
    import cv2
    import numpy as np
    from PIL import Image

    cached_path = scores_dir / f"{asset_path.stem}_clip_scores.json"
    if cached_path.exists():
        logger.info(f"  [CLIP] Cache hit: {cached_path.name}")
        return json.loads(cached_path.read_text())

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip_lib.load(config["clip"]["model_name"], device=device)
    brand_labels = config["clip"]["brand_labels"]

    # Extract representative frame
    suffix = asset_path.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        cap = cv2.VideoCapture(str(asset_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Sample 5 frames and average
        indices = np.linspace(0, total - 1, 5, dtype=int)
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
    else:
        img = cv2.imread(str(asset_path))
        frames = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB)]

    # CLIP inference on each frame
    text_tokens = clip_lib.tokenize(brand_labels).to(device)
    all_scores = {label: [] for label in brand_labels}

    with torch.inference_mode():
        text_features = model.encode_text(text_tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        for frame_rgb in frames:
            pil_img = Image.fromarray(frame_rgb)
            image_input = preprocess(pil_img).unsqueeze(0).to(device)
            image_features = model.encode_image(image_input)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            similarities = (image_features @ text_features.T).squeeze(0)
            probs = similarities.softmax(dim=-1).cpu().numpy()

            for label, prob in zip(brand_labels, probs):
                all_scores[label].append(float(prob))

    # Average across frames
    avg_scores = {label: float(np.mean(scores)) for label, scores in all_scores.items()}
    top_label = max(avg_scores, key=avg_scores.get)
    brand_match = float(np.mean(list(avg_scores.values())))

    # Cleanup
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

    result = {
        "asset_path": str(asset_path),
        "brand_match_score": brand_match,
        "top_label": top_label,
        "top_label_score": avg_scores[top_label],
        "all_scores": avg_scores,
    }

    cached_path.write_text(json.dumps(result, indent=2))
    return result


def run_emotion(asset_path: Path, config: dict, scores_dir: Path) -> dict:
    """Run HSEmotion facial emotion detection on video frames."""
    import cv2

    cached_path = scores_dir / f"{asset_path.stem}_emotion_scores.json"
    if cached_path.exists():
        logger.info(f"  [EMOTION] Cache hit: {cached_path.name}")
        return json.loads(cached_path.read_text())

    suffix = asset_path.suffix.lower()
    sample_every = config["emotion"]["sample_every_n"]

    # Try to import hsemotion
    try:
        from hsemotion.facial_emotions import HSEmotionRecognizer
    except ImportError:
        logger.warning("  [EMOTION] hsemotion not installed — skipping")
        return {"asset_path": str(asset_path), "skipped": True,
                "reason": "hsemotion not installed"}

    fer = HSEmotionRecognizer(model_name="enet_b0_8_best_afew")

    # Extract frames
    if suffix in VIDEO_EXTENSIONS:
        cap = cv2.VideoCapture(str(asset_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = []
        for i in range(0, total, sample_every):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
    else:
        img = cv2.imread(str(asset_path))
        frames = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB)] if img is not None else []

    if not frames:
        return {"asset_path": str(asset_path), "skipped": True,
                "reason": "no frames extracted"}

    # Run emotion detection
    emotion_counts: dict[str, int] = {}
    faces_found = 0
    total_frames_analyzed = 0

    for frame in frames:
        total_frames_analyzed += 1
        try:
            emotion, scores = fer.predict_emotions(frame, logits=False)
            if emotion:
                faces_found += 1
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        except Exception:
            continue

    # Summarize
    if faces_found == 0:
        dominant_emotion = "none"
        face_coverage = 0.0
        emotion_distribution = {}
    else:
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        face_coverage = faces_found / total_frames_analyzed
        emotion_distribution = {
            e: c / faces_found for e, c in emotion_counts.items()
        }

    # Map to valence score (-1 to 1)
    POSITIVE_EMOTIONS = {"happiness", "surprise"}
    NEGATIVE_EMOTIONS = {"anger", "disgust", "fear", "sadness"}
    positive_ratio = sum(
        emotion_distribution.get(e, 0) for e in POSITIVE_EMOTIONS
    )
    negative_ratio = sum(
        emotion_distribution.get(e, 0) for e in NEGATIVE_EMOTIONS
    )
    emotional_valence = float(positive_ratio - negative_ratio)

    # Cleanup
    del fer
    gc.collect()

    result = {
        "asset_path":           str(asset_path),
        "dominant_emotion":     dominant_emotion,
        "emotional_valence":    emotional_valence,   # -1 to 1
        "face_coverage":        face_coverage,        # 0-1, % frames with face
        "emotion_distribution": emotion_distribution,
        "frames_analyzed":      total_frames_analyzed,
        "faces_found":          faces_found,
    }

    cached_path.write_text(json.dumps(result, indent=2))
    return result




def run_mirofish(assets: list[Path], config: dict, campaign_dir: Path,
                 brand_context: str = "") -> dict:
    """
    MiroFish social simulation — runs via local MiroFish API.

    Args:
        assets: List of asset paths (not used directly, context comes from brand_context)
        config: Pipeline configuration
        campaign_dir: Directory of the campaign
        brand_context: Context string describing the brand/campaign for the simulation

    Returns:
        Dictionary with dummy sentiment values (placeholder until API report is parsed)
    """
    logger.info("  [MIROFISH] Running simulation via MiroFish API...")

    try:
        # Initialize the MiroFish client
        client = MiroFishClient(base_url="http://localhost:5001/api")

        # Use the first asset name as campaign name, or default
        campaign_name = assets[0].stem if assets else "campaign"

        # Run the simulation
        result = client.run_simulation(
            campaign_name=campaign_name,
            context=brand_context
        )

        logger.info("  [MIROFISH] Simulation completed successfully")

        # Log raw API response for debugging
        logger.info(f"Raw API Report Data: {result}")

        # Return the actual API response data
        return result

    except Exception as e:
        logger.error(f"  [MIROFISH] Simulation failed: {e}")
        # Return neutral scores on failure
        return {
            "positive_sentiment": 0.5,
            "negative_sentiment": 0.5,
            "virality_score":     0.5,
            "controversy_risk":   0.5,
            "source":             "error",
            "note":               f"Simulation failed: {str(e)}",
        }


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------

def compute_composite(
    tribe_result:    dict | None,
    saliency_result: dict | None,
    clip_result:     dict | None,
    emotion_result:  dict | None,
    mirofish_result: dict | None,
    weights:         dict,
) -> dict:
    """
    Combine all module scores into a weighted composite.

    Missing modules default to 0.5 (neutral) so the pipeline
    can run with any subset of modules enabled.
    """
    def safe_get(d, key, default=0.5):
        if d is None:
            return default
        return float(d.get(key, default))

    scores = {
        "neural_engagement": safe_get(tribe_result,    "neural_engagement"),
        "emotional_impact":  safe_get(tribe_result,    "emotional_impact"),
        "visual_attention":  safe_get(saliency_result, "center_bias"),
        "brand_consistency": safe_get(clip_result,     "brand_match_score"),
        "social_sentiment":  safe_get(mirofish_result, "positive_sentiment"),
        "facial_emotion":    max(0.0, (safe_get(emotion_result, "emotional_valence") + 1) / 2),
        "audio_engagement":  safe_get(tribe_result,    "language_engagement"),
    }

    # Weighted total
    total = sum(
        scores[key] * weights.get(key, 0.0)
        for key in scores
    )
    # Normalize by sum of active weights
    weight_sum = sum(weights.get(k, 0.0) for k in scores)
    if weight_sum > 0:
        total = total / weight_sum

    def grade(s):
        if s >= 0.70: return "A"
        if s >= 0.50: return "B"
        if s >= 0.30: return "C"
        return "D"

    return {
        "total_score":  round(total, 4),
        "grade":        grade(total),
        "breakdown":    {k: round(v, 4) for k, v in scores.items()},
        "weights_used": weights,
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline_a(
    campaign_dir: str,
    config: dict = None,
    brand_labels: list[str] = None,
    rois: dict | None = None,
    skip_modules: list[str] = None,
    only_modules: list[str] = None,
) -> dict:
    """
    Run Pipeline A on a campaign directory.

    Args:
        campaign_dir:  Path to campaign root (must contain assets/ folder)
        config:        Override default config (merged with DEFAULT_CONFIG)
        brand_labels:  CLIP brand labels e.g. ["sporty", "premium", "innovative"]
        rois:          Saliency ROI bounding boxes {name: (x1,y1,x2,y2)}
        skip_modules:  List of module names to skip
        only_modules:  If set, run only these modules

    Returns:
        Full pipeline results dict
    """
    campaign_path = Path(campaign_dir)
    if not campaign_path.exists():
        raise FileNotFoundError(f"Campaign directory not found: {campaign_dir}")

    # Merge config
    cfg = DEFAULT_CONFIG.copy()
    if config:
        for key, val in config.items():
            if isinstance(val, dict) and key in cfg:
                cfg[key].update(val)
            else:
                cfg[key] = val

    if brand_labels:
        cfg["clip"]["brand_labels"] = brand_labels

    # Apply skip/only
    skip = set(skip_modules or [])
    only = set(only_modules or [])
    for module in cfg["modules"]:
        if only:
            cfg["modules"][module]["enabled"] = (module in only)
        elif module in skip:
            cfg["modules"][module]["enabled"] = False

    # Setup directories
    scores_dir  = campaign_path / "scores"
    report_dir  = campaign_path / "report"
    scores_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    # Collect assets
    assets = collect_assets(campaign_path)
    if not assets:
        logger.warning("No assets found — aborting")
        return {}

    logger.info(f"\n{'='*60}")
    logger.info(f" NeuroAd Pipeline A — {campaign_path.name}")
    logger.info(f"{'='*60}")
    logger.info(f" Assets:  {len(assets)}")
    logger.info(f" Modules: {[m for m, c in cfg['modules'].items() if c['enabled']]}")
    logger.info(f"{'='*60}\n")

    t_pipeline_start = time.time()
    asset_results = []

    for i, asset in enumerate(assets, 1):
        logger.info(f"\n{'─'*50}")
        logger.info(f" Asset {i}/{len(assets)}: {asset.name}")
        logger.info(f"{'─'*50}")

        asset_scores = {"asset_path": str(asset), "asset_name": asset.name}
        t_asset_start = time.time()

        # ── TRIBE v2 ──────────────────────────────────────────────
        tribe_result = None
        if cfg["modules"]["tribe"]["enabled"]:
            logger.info("\n[1/5] TRIBE v2 Neural Scoring...")
            try:
                tribe_result = run_tribe(asset, cfg, scores_dir)
                asset_scores["tribe"] = tribe_result
                logger.info(
                    f"  neural_engagement={tribe_result.get('neural_engagement', 0):.3f} "
                    f"emotional_impact={tribe_result.get('emotional_impact', 0):.3f}"
                )
            except Exception as e:
                logger.error(f"  TRIBE failed: {e}")
                asset_scores["tribe"] = {"error": str(e)}

        # ── SALIENCY ──────────────────────────────────────────────
        saliency_result = None
        if cfg["modules"]["saliency"]["enabled"]:
            logger.info("\n[2/5] ViNet-S Saliency Scoring...")
            try:
                saliency_result = run_saliency(asset, cfg, scores_dir, rois=rois)
                asset_scores["saliency"] = saliency_result
                logger.info(
                    f"  center_bias={saliency_result.get('center_bias', 0):.3f} "
                    f"mean_saliency={saliency_result.get('mean_saliency', 0):.3f}"
                )
            except Exception as e:
                logger.error(f"  Saliency failed: {e}")
                asset_scores["saliency"] = {"error": str(e)}

        # ── CLIP ──────────────────────────────────────────────────
        clip_result = None
        if cfg["modules"]["clip"]["enabled"]:
            logger.info("\n[3/5] CLIP Brand Consistency...")
            try:
                clip_result = run_clip(asset, cfg, scores_dir)
                asset_scores["clip"] = clip_result
                logger.info(
                    f"  brand_match={clip_result.get('brand_match_score', 0):.3f} "
                    f"top_label='{clip_result.get('top_label', '')}'"
                )
            except Exception as e:
                logger.error(f"  CLIP failed: {e}")
                asset_scores["clip"] = {"error": str(e)}

        # ── EMOTION ───────────────────────────────────────────────
        emotion_result = None
        if cfg["modules"]["emotion"]["enabled"]:
            logger.info("\n[4/5] HSEmotion Facial Emotion...")
            try:
                emotion_result = run_emotion(asset, cfg, scores_dir)
                asset_scores["emotion"] = emotion_result
                logger.info(
                    f"  dominant={emotion_result.get('dominant_emotion', 'none')} "
                    f"valence={emotion_result.get('emotional_valence', 0):.3f} "
                    f"face_coverage={emotion_result.get('face_coverage', 0):.2f}"
                )
            except Exception as e:
                logger.error(f"  Emotion failed: {e}")
                asset_scores["emotion"] = {"error": str(e)}

        # ── LEMONADE SERVER (HARD RESET DISABLED - Qwen 3.5 9B with 96GB VRAM) ───────────
        # Lemonade server now runs permanently to support MiroFish embedding generation
        # during simulation without restarts or VRAM flushes
        # if cfg["modules"]["mirofish"]["enabled"]:
        #     restart_lemonade_server()

        # ── MIROFISH ──────────────────────────────────────────────
        mirofish_result = None
        mirofish_failed = False
        if cfg["modules"]["mirofish"]["enabled"]:
            logger.info("\n[5/5] MiroFish Social Simulation (API)...")
            try:
                mirofish_result = run_mirofish(
                    assets=assets,
                    config=cfg,
                    campaign_dir=campaign_path,
                    brand_context="Apple vs Samsung" # Can become dynamic later
                )
                asset_scores["mirofish"] = mirofish_result
            except Exception as e:
                logger.error(f"  MiroFish API failed: {e}")
                mirofish_result = {"error": str(e), "failed": True}
                asset_scores["mirofish"] = mirofish_result
                mirofish_failed = True
        else:
            logger.info("\n[5/5] MiroFish — skipped (enable when API ready)")
            mirofish_result = {"positive_sentiment": 0.5}

        # ── COMPOSITE ─────────────────────────────────────────────
        composite = compute_composite(
            tribe_result=tribe_result,
            saliency_result=saliency_result,
            clip_result=clip_result,
            emotion_result=emotion_result,
            mirofish_result=mirofish_result,
            weights=cfg["weights"],
        )
        asset_scores["composite"] = composite

        elapsed = time.time() - t_asset_start
        asset_scores["processing_time_s"] = round(elapsed, 1)

        logger.info(f"\n  ══ COMPOSITE SCORE: {composite['total_score']:.3f} "
                    f"(Grade {composite['grade']}) ══")
        logger.info(f"  Time: {elapsed:.0f}s")

        asset_results.append(asset_scores)

        # Save interim results
        interim_path = scores_dir / "pipeline_results_interim.json"
        interim_path.write_text(json.dumps(asset_results, indent=2))

    # ── FINAL REPORT ──────────────────────────────────────────────
    pipeline_elapsed = time.time() - t_pipeline_start

    # Sort by composite score
    asset_results.sort(
        key=lambda x: x.get("composite", {}).get("total_score", 0),
        reverse=True
    )

    # Track failed assets (those with errors in any module)
    failed_assets = []
    for r in asset_results:
        asset_name = r.get("asset_name", "unknown")
        has_error = False
        # Check all module results for errors
        for module_name in ["tribe", "saliency", "clip", "emotion", "mirofish"]:
            module_result = r.get(module_name, {})
            if isinstance(module_result, dict) and ("error" in module_result or module_result.get("failed")):
                has_error = True
                break
        if has_error:
            failed_assets.append(asset_name)

    report = {
        "campaign":        campaign_path.name,
        "n_assets":        len(assets),
        "modules_run":     [m for m, c in cfg["modules"].items() if c["enabled"]],
        "brand_labels":    cfg["clip"]["brand_labels"],
        "total_time_s":    round(pipeline_elapsed, 1),
        "failed_assets":   failed_assets,
        "ranking":         [
            {
                "rank":          i + 1,
                "asset":         r["asset_name"],
                "total_score":   r.get("composite", {}).get("total_score", 0),
                "grade":         r.get("composite", {}).get("grade", "?"),
                "breakdown":     r.get("composite", {}).get("breakdown", {}),
            }
            for i, r in enumerate(asset_results)
        ],
        "assets":          asset_results,
    }

    # Save final report
    final_path = report_dir / "pipeline_a_results.json"
    final_path.write_text(json.dumps(report, indent=2))

    # Save scores summary
    scores_summary = scores_dir / "pipeline_results_final.json"
    scores_summary.write_text(json.dumps(asset_results, indent=2))

    logger.info(f"\n{'='*60}")
    logger.info(f" Pipeline A Complete — {campaign_path.name}")
    logger.info(f" Total time: {pipeline_elapsed/60:.1f} minutes")
    logger.info(f" Report: {final_path}")
    logger.info(f"{'='*60}")
    logger.info("\n RANKING:")
    for entry in report["ranking"]:
        logger.info(
            f"  #{entry['rank']} {entry['asset']:30s} "
            f"Score: {entry['total_score']:.3f} (Grade {entry['grade']})"
        )

    # Log failed assets
    if failed_assets:
        logger.warning(f"\n FAILED ASSETS ({len(failed_assets)}):")
        for asset_name in failed_assets:
            logger.warning(f"  - {asset_name}")
    else:
        logger.info("\n All assets processed successfully!")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NeuroAd Pipeline A — Score existing ad creatives"
    )
    parser.add_argument(
        "campaign_dir",
        help="Path to campaign directory (must contain assets/ folder)"
    )
    parser.add_argument(
        "--brand-labels", nargs="+", default=None,
        metavar="LABEL",
        help='CLIP brand labels e.g. --brand-labels "sporty" "premium" "innovative"'
    )
    parser.add_argument(
        "--skip", nargs="+", default=[],
        choices=["tribe", "saliency", "clip", "emotion", "mirofish"],
        help="Skip specific modules"
    )
    parser.add_argument(
        "--only", nargs="+", default=[],
        choices=["tribe", "saliency", "clip", "emotion", "mirofish"],
        help="Run only specific modules"
    )
    parser.add_argument(
        "--roi", action="append", metavar="NAME:x1,y1,x2,y2",
        help="Saliency ROI e.g. --roi product:100,200,400,500"
    )
    parser.add_argument(
        "--saliency-model", default="vinet_s",
        choices=["vinet_s", "vinet_a"],
        help="Saliency model variant (default: vinet_s)"
    )
    parser.add_argument(
        "--device", default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Compute device (default: auto)"
    )

    args = parser.parse_args()

    # Parse ROIs
    rois = {}
    if args.roi:
        for roi_str in args.roi:
            name, coords = roi_str.split(":")
            x1, y1, x2, y2 = map(int, coords.split(","))
            rois[name] = (x1, y1, x2, y2)

    config_override = {
        "saliency": {"model_variant": args.saliency_model},
    }
    if args.device != "auto":
        config_override["tribe"]    = {"device": args.device}
        config_override["saliency"] = {"device": args.device}
        config_override["clip"]     = {"device": args.device}
        config_override["emotion"]  = {"device": args.device}

    report = run_pipeline_a(
        campaign_dir=args.campaign_dir,
        config=config_override,
        brand_labels=args.brand_labels,
        rois=rois or None,
        skip_modules=args.skip,
        only_modules=args.only,
    )

    print(f"\nDone. Report saved to: {Path(args.campaign_dir) / 'report' / 'pipeline_a_results.json'}")
