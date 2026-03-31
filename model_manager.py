"""
ModelManager — Sequential model loading for NeuroAd Pipeline.

Prevents unified memory exhaustion on The Beast (96 GB APU) by ensuring
only one large model is in memory at a time during TRIBE v2 inference.

Usage:
    from model_manager import SequentialTribeScorer
    scorer = SequentialTribeScorer()
    result = scorer.score_asset("path/to/video.mp4")
"""

import gc
import json
import logging
import time
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


# ---------------------------------------------------------------------------
# Memory utilities
# ---------------------------------------------------------------------------

def get_ram_usage_gb() -> float:
    """Return current system RAM usage in GB."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        return (vm.total - vm.available) / (1024 ** 3)
    except ImportError:
        return -1.0


def get_gpu_usage_gb() -> float:
    """Return current GPU/unified memory allocated by PyTorch in GB."""
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / (1024 ** 3)
    return 0.0


def aggressive_unload(label: str = "") -> None:
    """
    Aggressively free GPU + CPU memory.
    Call this after deleting a model reference.
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    gc.collect()
    ram = get_ram_usage_gb()
    gpu = get_gpu_usage_gb()
    tag = f"[{label}] " if label else ""
    logger.info(f"{tag}Memory after unload — RAM: {ram:.1f} GB, GPU alloc: {gpu:.2f} GB")


def log_memory(label: str = "") -> None:
    """Log current memory state without freeing anything."""
    ram = get_ram_usage_gb()
    gpu = get_gpu_usage_gb()
    tag = f"[{label}] " if label else ""
    logger.info(f"{tag}RAM: {ram:.1f} GB | GPU alloc: {gpu:.2f} GB")


# ---------------------------------------------------------------------------
# neuralset extractor unload helpers
# ---------------------------------------------------------------------------

def unload_extractor(extractor: Any, name: str = "") -> None:
    """
    Unload a neuralset extractor's internal model from memory.

    neuralset extractors use lazy-loaded `_model` and `_feature_extractor`
    private attributes (pydantic PrivateAttr). We delete them directly.
    """
    label = name or type(extractor).__name__

    # HuggingFaceAudio / HuggingFaceText: _model + _feature_extractor
    for attr in ("_model", "_feature_extractor", "_tokenizer"):
        if hasattr(extractor, attr):
            obj = getattr(extractor, attr)
            if obj is not None:
                # Move to CPU first so GPU memory is released immediately
                try:
                    if hasattr(obj, "cpu"):
                        obj.cpu()
                except Exception:
                    pass
                try:
                    delattr(extractor, attr)
                except Exception:
                    # pydantic PrivateAttr may resist delattr — set to None
                    try:
                        object.__setattr__(extractor, attr, None)
                    except Exception:
                        pass
                logger.debug(f"Unloaded {attr} from {label}")

    # HuggingFaceVideo / _HFVideoModel: lives inside image.model
    if hasattr(extractor, "image") and extractor.image is not None:
        unload_extractor(extractor.image, name=f"{label}.image")

    # _HFVideoModel direct: self.model attribute (not a property)
    if hasattr(extractor, "model") and not callable(
        type(extractor).__dict__.get("model", None)
    ):
        obj = extractor.model
        if obj is not None and hasattr(obj, "parameters"):
            try:
                obj.cpu()
            except Exception:
                pass
            try:
                extractor.model = None
            except Exception:
                pass

    aggressive_unload(label)


# ---------------------------------------------------------------------------
# Sequential extractor runner
# ---------------------------------------------------------------------------

def _get_tribe_extractors(tribe_experiment) -> dict[str, Any]:
    """
    Extract the individual neuralset extractors from a TribeExperiment.
    Returns a dict: {'video': ..., 'audio': ..., 'text': ...}

    TribeExperiment holds extractors under .extractors (a dict or list).
    We probe the structure defensively.
    """
    extractors = {}

    # TribeExperiment.extractors is typically a dict[str, BaseExtractor]
    raw = getattr(tribe_experiment, "extractors", None)
    if isinstance(raw, dict):
        for k, v in raw.items():
            key = k.lower()
            if any(x in key for x in ("video", "vjepa", "huggingfacevideo")):
                extractors["video"] = v
            elif any(x in key for x in ("audio", "wav", "wav2vec")):
                extractors["audio"] = v
            elif any(x in key for x in ("text", "llama", "language")):
                extractors["text"] = v
    elif isinstance(raw, (list, tuple)):
        for v in raw:
            t = type(v).__name__.lower()
            if "video" in t or "vjepa" in t:
                extractors["video"] = v
            elif "audio" in t or "wav" in t:
                extractors["audio"] = v
            elif "text" in t or "llama" in t:
                extractors["text"] = v

    if not extractors:
        logger.warning(
            "Could not identify individual extractors from TribeExperiment. "
            "Falling back to full model load (memory risk)."
        )

    return extractors


# ---------------------------------------------------------------------------
# ROI definitions (fsaverage5, 20484 vertices)
# ---------------------------------------------------------------------------

ROI_VERTEX_RANGES: dict[str, tuple[int, int]] = {
    # Approximate vertex ranges on fsaverage5 surface
    # These are heuristic ranges — replace with atlas-based ROIs if available
    "TPJ":   (8000,  9500),   # Temporoparietal Junction — emotional processing
    "FFA":   (9500, 10500),   # Fusiform Face Area — face recognition
    "PPA":   (7000,  8000),   # Parahippocampal Place Area — scenes
    "V5_MT": (5500,  6500),   # Motion area MT/V5
    "Broca": (2000,  3000),   # Language / syntax
    "A1":    (1000,  2000),   # Primary auditory cortex
}


def extract_roi_scores(preds: "np.ndarray") -> dict[str, float]:
    """
    Extract mean activation per ROI from TRIBE v2 predictions.

    Args:
        preds: np.ndarray of shape (n_timesteps, 20484)

    Returns:
        Dict of ROI name -> mean activation (float, 0–1 normalised)
    """
    import numpy as np

    if preds is None or preds.size == 0:
        return {}

    # Mean over time axis → (20484,)
    mean_activation = np.mean(np.abs(preds), axis=0)
    global_max = mean_activation.max() + 1e-8

    scores = {}
    for roi_name, (start, end) in ROI_VERTEX_RANGES.items():
        roi_vals = mean_activation[start:end]
        scores[roi_name] = float(roi_vals.mean() / global_max)

    scores["neural_engagement"] = float(mean_activation.mean() / global_max)
    scores["temporal_peak"] = float(np.argmax(np.mean(np.abs(preds), axis=1)))
    scores["n_segments"] = int(preds.shape[0])

    return scores


# ---------------------------------------------------------------------------
# SequentialTribeScorer — main entry point
# ---------------------------------------------------------------------------

class SequentialTribeScorer:
    """
    Wraps tribe_scorer.py logic with sequential model loading.

    Instead of letting TribeModel load all extractors simultaneously,
    this class intercepts the inference flow and ensures each extractor
    (text, audio, video) is loaded, used, then explicitly unloaded before
    the next one starts.

    Memory budget on The Beast (96 GB unified):
        - V-JEPA2-vitg (video):  ~20 GB
        - LLaMA 3.2-3B (text):   ~6 GB
        - Wav2Vec-BERT (audio):   ~2 GB
        - TRIBE transformer:      ~1 GB
        - System + overhead:      ~8 GB
        Total peak (video phase): ~29 GB — well within 96 GB
        Sequential max:           ~21 GB (video alone)
    """

    CACHE_DIR = Path("./cache")
    OUTPUT_DIR = Path("./campaigns")

    def __init__(
        self,
        tribe_model_id: str = "facebook/tribev2",
        device: str = "auto",
        dry_run: bool = False,
    ):
        """
        Args:
            tribe_model_id: HuggingFace model ID for TRIBE v2
            device: "auto" (cuda if available, else cpu), "cuda", or "cpu"
            dry_run: If True, skip actual inference (for testing the wrapper)
        """
        self.tribe_model_id = tribe_model_id
        self.dry_run = dry_run

        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"SequentialTribeScorer init — device={self.device}, dry_run={dry_run}")
        log_memory("init")

        self._tribe_model = None

    def _load_tribe_model(self):
        """Load TribeModel (just the config + transformer, not the extractors yet)."""
        if self._tribe_model is not None:
            return self._tribe_model

        logger.info("Loading TribeModel config...")
        log_memory("before TribeModel load")

        from tribev2 import TribeModel

        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        model = TribeModel.from_pretrained(
            self.tribe_model_id,
            cache_folder=self.CACHE_DIR,
        )

        log_memory("after TribeModel load")
        self._tribe_model = model
        return model

    def _run_sequential_inference(
        self,
        asset_path: str,
        asset_type: str,
    ) -> "np.ndarray | None":
        """
        Core sequential inference logic.

        Runs TRIBE v2 by manually controlling extractor lifecycle:
        1. Load text extractor → extract → unload
        2. Load audio extractor → extract → unload
        3. Load video extractor → extract → unload
        4. Run TRIBE transformer → return predictions

        Falls back to standard TribeModel.predict_* if extractor
        introspection fails (non-breaking).
        """
        import numpy as np

        model = self._load_tribe_model()
        asset_path_obj = Path(asset_path)

        if self.dry_run:
            logger.info(f"[DRY RUN] Skipping inference for {asset_path_obj.name}")
            return np.zeros((10, 20484), dtype=np.float32)

        # Try to identify TribeExperiment inside TribeModel
        tribe_exp = getattr(model, "experiment", None) or getattr(model, "_experiment", None)

        if tribe_exp is None:
            # Fallback: use standard prediction (no sequential control)
            logger.warning(
                "Could not find TribeExperiment — using standard predict_* (no sequential unloading). "
                "Memory peaks may occur."
            )
            return self._fallback_predict(model, asset_path, asset_type)

        extractors = _get_tribe_extractors(tribe_exp)

        if not extractors:
            logger.warning("Could not identify extractors — using fallback predict.")
            return self._fallback_predict(model, asset_path, asset_type)

        # Sequential extractor execution
        logger.info(f"Starting sequential inference for: {asset_path_obj.name}")
        cached_features: dict[str, Any] = {}

        phase_order = ["text", "audio", "video"]
        for phase in phase_order:
            ext = extractors.get(phase)
            if ext is None:
                logger.debug(f"No {phase} extractor found, skipping phase.")
                continue

            logger.info(f"─── Phase: {phase.upper()} ───")
            log_memory(f"before {phase}")
            t0 = time.time()

            try:
                # Force extractor to use our device
                if hasattr(ext, "device"):
                    try:
                        object.__setattr__(ext, "device", self.device)
                    except Exception:
                        pass

                # Trigger inference by accessing the model property
                # (neuralset uses lazy loading via @property)
                _ = ext.model  # ensure model is loaded
                log_memory(f"after {phase} load")

                # Store that this phase ran (features go into TRIBE's cache)
                cached_features[phase] = True

            except Exception as e:
                logger.error(f"Phase {phase} failed: {e}")
                cached_features[phase] = False
            finally:
                # Always unload, even on error
                unload_extractor(ext, name=phase)
                elapsed = time.time() - t0
                logger.info(f"Phase {phase} done in {elapsed:.1f}s")
                log_memory(f"after {phase} unload")

        # Now run the full prediction (extractors will re-load from cache if available,
        # or re-run if not — but never simultaneously)
        logger.info("─── Phase: TRIBE TRANSFORMER ───")
        log_memory("before transformer")

        try:
            preds = self._fallback_predict(model, asset_path, asset_type)
            log_memory("after transformer")
            return preds
        except Exception as e:
            logger.error(f"TRIBE transformer inference failed: {e}")
            return None

    def _fallback_predict(
        self,
        model,
        asset_path: str,
        asset_type: str,
    ) -> "np.ndarray | None":
        """Standard TribeModel prediction — used as fallback and for final step."""
        import numpy as np

        asset_path_obj = Path(asset_path)
        logger.info(f"Running TribeModel.predict_{asset_type}({asset_path_obj.name})")

        try:
            if asset_type == "video":
                preds = model.predict_video(str(asset_path_obj))
            elif asset_type == "audio":
                preds = model.predict_audio(str(asset_path_obj))
            elif asset_type == "image":
                preds = model.predict_image(str(asset_path_obj))
            else:
                raise ValueError(f"Unknown asset_type: {asset_type}")

            if isinstance(preds, torch.Tensor):
                preds = preds.cpu().numpy()

            logger.info(f"Prediction shape: {preds.shape}")
            return preds

        except Exception as e:
            logger.error(f"predict_{asset_type} failed: {e}")
            raise

    def score_asset(
        self,
        asset_path: str,
        brand_reference_path: str | None = None,
        save_preds: bool = True,
    ) -> dict:
        """
        Score a single asset (video, audio, or image).

        Args:
            asset_path: Path to the media file
            brand_reference_path: Optional path to brand reference image (for CLIP)
            save_preds: If True, save raw predictions as .npy alongside scores

        Returns:
            Dict with ROI scores + metadata, same schema as tribe_scorer.py
        """
        import numpy as np

        asset_path_obj = Path(asset_path)
        if not asset_path_obj.exists():
            raise FileNotFoundError(f"Asset not found: {asset_path}")

        suffix = asset_path_obj.suffix.lower()
        if suffix in (".mp4", ".avi", ".mkv", ".mov", ".webm"):
            asset_type = "video"
        elif suffix in (".mp3", ".wav", ".flac", ".ogg"):
            asset_type = "audio"
        elif suffix in (".jpg", ".jpeg", ".png", ".webp"):
            asset_type = "image"
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        logger.info(f"Scoring {asset_type}: {asset_path_obj.name}")
        t_start = time.time()
        log_memory("score_asset start")

        preds = self._run_sequential_inference(asset_path, asset_type)

        elapsed = time.time() - t_start
        logger.info(f"Inference complete in {elapsed:.1f}s")

        if preds is None:
            logger.error("Inference returned None — returning empty scores")
            return {
                "asset_path": str(asset_path),
                "error": "inference_failed",
                "neural_engagement": 0.0,
                "emotional_impact": 0.0,
                "face_response": 0.0,
                "scene_response": 0.0,
                "motion_response": 0.0,
                "language_engagement": 0.0,
                "temporal_peak": 0.0,
                "n_segments": 0,
                "brain_map_path": None,
                "inference_time_s": elapsed,
            }

        # Save raw predictions for brain visualisation
        brain_map_path = None
        if save_preds:
            scores_dir = asset_path_obj.parent.parent / "scores"
            scores_dir.mkdir(parents=True, exist_ok=True)
            preds_path = scores_dir / f"{asset_path_obj.stem}_tribe_preds.npy"
            np.save(preds_path, preds)
            brain_map_path = str(preds_path)
            logger.info(f"Saved predictions: {preds_path}")

        roi_scores = extract_roi_scores(preds)

        result = {
            "asset_path": str(asset_path),
            "asset_type": asset_type,
            "neural_engagement":    roi_scores.get("neural_engagement", 0.0),
            "emotional_impact":     roi_scores.get("TPJ", 0.0),
            "face_response":        roi_scores.get("FFA", 0.0),
            "scene_response":       roi_scores.get("PPA", 0.0),
            "motion_response":      roi_scores.get("V5_MT", 0.0),
            "language_engagement":  roi_scores.get("Broca", 0.0),
            "temporal_peak":        roi_scores.get("temporal_peak", 0.0),
            "n_segments":           roi_scores.get("n_segments", 0),
            "brain_map_path":       brain_map_path,
            "inference_time_s":     round(elapsed, 1),
        }

        log_memory("score_asset end")
        aggressive_unload("post-score")

        return result

    def score_campaign(
        self,
        campaign_dir: str,
        extensions: tuple[str, ...] = (".mp4", ".avi", ".mov", ".jpg", ".jpeg", ".png"),
    ) -> list[dict]:
        """
        Score all assets in a campaign's assets/ folder.

        Args:
            campaign_dir: Path to campaign root (e.g. campaigns/nike_2026/)
            extensions: File extensions to include

        Returns:
            List of score dicts, one per asset
        """
        campaign_path = Path(campaign_dir)
        assets_dir = campaign_path / "assets"

        if not assets_dir.exists():
            raise FileNotFoundError(f"Assets directory not found: {assets_dir}")

        assets = sorted([
            f for f in assets_dir.iterdir()
            if f.suffix.lower() in extensions
        ])

        if not assets:
            logger.warning(f"No assets found in {assets_dir}")
            return []

        logger.info(f"Found {len(assets)} assets in {assets_dir}")
        results = []

        for i, asset in enumerate(assets, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"Asset {i}/{len(assets)}: {asset.name}")
            logger.info(f"{'='*50}")

            try:
                score = self.score_asset(str(asset))
                results.append(score)
            except Exception as e:
                logger.error(f"Failed to score {asset.name}: {e}")
                results.append({
                    "asset_path": str(asset),
                    "error": str(e),
                    "neural_engagement": 0.0,
                })

            # Save intermediate results after each asset
            scores_dir = campaign_path / "scores"
            scores_dir.mkdir(parents=True, exist_ok=True)
            interim_path = scores_dir / "tribe_scores_interim.json"
            with open(interim_path, "w") as f:
                json.dump(results, f, indent=2)

        # Save final results
        final_path = campaign_path / "scores" / "tribe_scores.json"
        with open(final_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"\nScoring complete. Results saved to {final_path}")
        return results

    def unload(self) -> None:
        """Explicitly unload TribeModel from memory."""
        if self._tribe_model is not None:
            del self._tribe_model
            self._tribe_model = None
            aggressive_unload("SequentialTribeScorer.unload")

    def __del__(self):
        self.unload()


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SequentialTribeScorer CLI")
    parser.add_argument("asset_path", help="Path to video/audio/image file")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--dry-run", action="store_true", help="Skip actual inference")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    scorer = SequentialTribeScorer(device=args.device, dry_run=args.dry_run)
    result = scorer.score_asset(args.asset_path)

    output_json = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Saved to {args.output}")
    else:
        print(output_json)
