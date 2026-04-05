#!/usr/bin/env python3
"""
saliency_scorer.py — ViNet-S Video Saliency Scorer for NeuroAd Pipeline

Wraps ViNet++ (ViNet-S) to produce:
- Per-frame saliency maps (numpy arrays)
- Overlay PNGs (heatmap over original frame)
- Attention scores for user-defined ROIs (product, logo, CTA bounding boxes)
- Summary JSON compatible with composite_scorer.py

Usage:
    from saliency_scorer import SaliencyScorer

    scorer = SaliencyScorer()
    result = scorer.score_asset(
        asset_path="campaigns/nike/assets/spot.mp4",
        rois={
            "product": (100, 200, 400, 500),  # (x1, y1, x2, y2) in pixels
            "logo":    (10,  10,  120, 80),
        }
    )
    print(result["product_attention"])  # 0.0 - 1.0

CLI:
    python saliency_scorer.py campaigns/nike/assets/spot.mp4
    python saliency_scorer.py campaigns/nike/assets/spot.mp4 --frames 8
"""

import gc
import json
import logging
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

VINET_S_DIR = Path(__file__).parent / "tools" / "ViNet_v2" / "ViNet_S"
WEIGHTS_DIR  = Path(__file__).parent / "tools" / "ViNet_v2" / "saved_models"

# Expected checkpoint name after unzipping weights.zip
# Adjust if the zip extracts to a different name
CHECKPOINT_NAME = "DHF1K_vinet_s_rootgrouped_32_bs8_kld_cc.pt"


# ---------------------------------------------------------------------------
# Frame extraction helpers
# ---------------------------------------------------------------------------

def extract_frames(video_path: str, n_frames: int = 32) -> list[np.ndarray]:
    """
    Extract n_frames evenly spaced frames from a video.

    Returns list of BGR numpy arrays (H, W, 3).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps   = cap.get(cv2.CAP_PROP_FPS)
    duration = total / fps if fps > 0 else 0

    indices = np.linspace(0, total - 1, n_frames, dtype=int)
    frames = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
        else:
            # Repeat last frame if read fails
            if frames:
                frames.append(frames[-1].copy())

    cap.release()

    if not frames:
        raise ValueError(f"Could not extract any frames from: {video_path}")

    logger.info(
        f"Extracted {len(frames)} frames from {Path(video_path).name} "
        f"({duration:.1f}s, {total} total frames)"
    )
    return frames


def extract_image_frames(image_path: str, n_frames: int = 32) -> list[np.ndarray]:
    """For images: tile the same frame n_frames times (ViNet expects a clip)."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    return [img.copy() for _ in range(n_frames)]


def preprocess_frames(
    frames: list[np.ndarray],
    target_size: tuple[int, int] = (224, 384),  # H, W — ViNet-S default
) -> torch.Tensor:
    """
    Convert BGR frames to ViNet-S input tensor.

    Returns: (1, 3, T, H, W) float32 tensor, normalized to [0, 1]
    """
    from torchvision import transforms

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(target_size),
        transforms.ToTensor(),
    ])

    tensors = []
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        t = transform(rgb)  # (3, H, W)
        tensors.append(t)

    clip = torch.stack(tensors, dim=1)  # (3, T, H, W)
    clip = clip.unsqueeze(0)            # (1, 3, T, H, W)
    return clip.float()


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def find_checkpoint() -> Path | None:
    """Search for ViNet-S checkpoint in known locations."""
    candidates = [
        WEIGHTS_DIR / CHECKPOINT_NAME,
        VINET_S_DIR / "saved_models" / CHECKPOINT_NAME,
        VINET_S_DIR / CHECKPOINT_NAME,
        Path(__file__).parent / "tools" / "ViNet_v2" / CHECKPOINT_NAME,
    ]
    # Also search recursively in weights dir
    for root in [WEIGHTS_DIR, Path(__file__).parent / "tools" / "ViNet_v2"]:
        if root.exists():
            for p in root.rglob("*.pt"):
                if "vinet_s" in p.name.lower() or "ViNet_S" in str(p):
                    candidates.append(p)

    for path in candidates:
        if path.exists():
            logger.info(f"Found checkpoint: {path}")
            return path

    return None


def load_vinet_s(checkpoint_path: Path, device: str = "cuda") -> Any:
    """
    Load ViNet-S model from checkpoint.
    Adds ViNet_S dir to sys.path to import model code.
    """
    vinet_s_str = str(VINET_S_DIR)
    if vinet_s_str not in sys.path:
        sys.path.insert(0, vinet_s_str)
    # Also need model_utils from same dir
    tools_vinet = str(VINET_S_DIR)
    if tools_vinet not in sys.path:
        sys.path.insert(0, tools_vinet)

    from ViNet_S_model import VideoSaliencyModel  # type: ignore

    model = VideoSaliencyModel(
        num_hier=3,
        use_upsample=True,
        num_clips=32,
    )

    state = torch.load(checkpoint_path, map_location="cpu")
    # Handle DataParallel checkpoints
    if any(k.startswith("module.") for k in state.keys()):
        from collections import OrderedDict
        state = OrderedDict((k.replace("module.", "", 1), v) for k, v in state.items())

    model.load_state_dict(state, strict=False)
    model = model.to(device)
    model.eval()
    logger.info(f"ViNet-S loaded on {device}")
    return model


# ---------------------------------------------------------------------------
# Saliency inference
# ---------------------------------------------------------------------------

@torch.inference_mode()
def run_saliency(
    model: Any,
    clip: torch.Tensor,
    device: str = "cuda",
    original_size: tuple[int, int] | None = None,
) -> np.ndarray:
    """
    Run ViNet-S inference on a clip tensor.

    Args:
        model: loaded ViNet-S model
        clip: (1, 3, T, H, W) tensor
        device: cuda or cpu
        original_size: (H, W) to resize output to

    Returns:
        saliency_map: (H, W) float32 array, values 0-1
    """
    clip = clip.to(device)
    output = model(clip)  # (1, 1, H', W') or (1, H', W')

    # Normalize output shape
    if output.dim() == 4:
        sal = output[0, 0]
    elif output.dim() == 3:
        sal = output[0]
    else:
        sal = output.squeeze()

    sal = sal.cpu().float().numpy()

    # Normalize to 0-1
    sal_min, sal_max = sal.min(), sal.max()
    if sal_max > sal_min:
        sal = (sal - sal_min) / (sal_max - sal_min)
    else:
        sal = np.zeros_like(sal)

    # Resize to original frame size
    if original_size is not None:
        h, w = original_size
        sal = cv2.resize(sal, (w, h), interpolation=cv2.INTER_LINEAR)

    return sal.astype(np.float32)


# ---------------------------------------------------------------------------
# ROI attention scoring
# ---------------------------------------------------------------------------

def score_roi(
    saliency_map: np.ndarray,
    roi: tuple[int, int, int, int],
) -> float:
    """
    Score attention within a bounding box ROI.

    Args:
        saliency_map: (H, W) float32 array, values 0-1
        roi: (x1, y1, x2, y2) in pixels

    Returns:
        attention score 0-1 (mean saliency in ROI / mean saliency globally)
        Scores > 1.0 mean the ROI is more salient than average (capped at 1.0)
    """
    x1, y1, x2, y2 = roi
    h, w = saliency_map.shape

    # Clamp to image bounds
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h))

    if x2 <= x1 or y2 <= y1:
        return 0.0

    roi_sal   = saliency_map[y1:y2, x1:x2].mean()
    global_sal = saliency_map.mean()

    if global_sal < 1e-8:
        return 0.0

    # Normalized: how much more attention does this ROI get vs average?
    score = float(roi_sal / global_sal)
    return min(score, 1.0)  # cap at 1.0 for composite scorer compatibility


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def create_heatmap_overlay(
    frame: np.ndarray,
    saliency_map: np.ndarray,
    alpha: float = 0.5,
    colormap: int = cv2.COLORMAP_JET,
) -> np.ndarray:
    """
    Overlay saliency heatmap on original frame.

    Returns BGR numpy array.
    """
    h, w = frame.shape[:2]
    sal_resized = cv2.resize(saliency_map, (w, h))

    # Convert to uint8 heatmap
    sal_uint8 = (sal_resized * 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(sal_uint8, colormap)

    # Blend
    overlay = cv2.addWeighted(frame, 1 - alpha, heatmap, alpha, 0)
    return overlay


def save_saliency_outputs(
    frames: list[np.ndarray],
    saliency_maps: list[np.ndarray],
    output_dir: Path,
    asset_stem: str,
    rois: dict[str, tuple[int, int, int, int]] | None = None,
    save_every_n: int = 8,
) -> dict[str, str]:
    """
    Save saliency overlay PNGs and mean saliency map.

    Returns dict of output paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    # Mean saliency map
    mean_sal = np.mean(saliency_maps, axis=0)
    mean_sal_path = output_dir / f"{asset_stem}_saliency_mean.npy"
    np.save(mean_sal_path, mean_sal)
    paths["mean_saliency_npy"] = str(mean_sal_path)

    # Mean saliency PNG (standalone heatmap)
    sal_uint8 = (mean_sal * 255).astype(np.uint8)
    heatmap_png = cv2.applyColorMap(sal_uint8, cv2.COLORMAP_JET)
    heatmap_path = output_dir / f"{asset_stem}_saliency_heatmap.png"
    cv2.imwrite(str(heatmap_path), heatmap_png)
    paths["heatmap_png"] = str(heatmap_path)

    # Representative overlay frames
    overlay_paths = []
    step = max(1, len(frames) // save_every_n)
    for i in range(0, len(frames), step):
        frame = frames[i]
        sal   = saliency_maps[i]
        overlay = create_heatmap_overlay(frame, sal)

        # Draw ROI boxes if provided
        if rois:
            for roi_name, (x1, y1, x2, y2) in rois.items():
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(overlay, roi_name, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        out_path = output_dir / f"{asset_stem}_saliency_frame{i:03d}.png"
        cv2.imwrite(str(out_path), overlay)
        overlay_paths.append(str(out_path))

    paths["overlay_frames"] = overlay_paths
    if overlay_paths:
        paths["overlay_representative"] = overlay_paths[len(overlay_paths) // 2]

    logger.info(f"Saved saliency outputs to {output_dir}")
    return paths


# ---------------------------------------------------------------------------
# Main scorer class
# ---------------------------------------------------------------------------

class SaliencyScorer:
    """
    ViNet-S based video saliency scorer for NeuroAd Pipeline.

    Produces per-frame saliency maps, overlay PNGs, and ROI attention scores.
    Compatible with composite_scorer.py score schema.
    """

    def __init__(
        self,
        checkpoint_path: str | None = None,
        device: str = "auto",
        n_frames: int = 32,
    ):
        """
        Args:
            checkpoint_path: Path to ViNet-S .pt checkpoint.
                             Auto-detected if None.
            device: "auto", "cuda", or "cpu"
            n_frames: Number of frames to sample per clip (32 = ViNet-S default)
        """
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.n_frames = n_frames
        self._model = None
        self._checkpoint_path = checkpoint_path

        logger.info(f"SaliencyScorer init — device={self.device}, n_frames={n_frames}")

    def _ensure_model(self) -> Any:
        """Lazy-load ViNet-S model."""
        if self._model is not None:
            return self._model

        # Find checkpoint
        if self._checkpoint_path:
            ckpt = Path(self._checkpoint_path)
        else:
            ckpt = find_checkpoint()

        if ckpt is None:
            raise FileNotFoundError(
                "ViNet-S checkpoint not found. "
                "Please unzip weights.zip and ensure the .pt file is in "
                f"{WEIGHTS_DIR} or pass checkpoint_path explicitly."
            )

        self._model = load_vinet_s(ckpt, device=self.device)
        return self._model

    def score_asset(
        self,
        asset_path: str,
        rois: dict[str, tuple[int, int, int, int]] | None = None,
        save_outputs: bool = True,
    ) -> dict:
        """
        Score a single video or image asset.

        Args:
            asset_path: Path to .mp4, .avi, .mov, .jpg, .png etc.
            rois: Optional dict of named bounding boxes {name: (x1, y1, x2, y2)}
                  e.g. {"product": (100, 200, 400, 500), "logo": (10, 10, 80, 60)}
                  Coordinates in pixels of the original frame.
            save_outputs: Save saliency maps and overlay PNGs to scores/ dir

        Returns:
            Dict with saliency scores, compatible with composite_scorer.py
        """
        asset_path_obj = Path(asset_path)
        if not asset_path_obj.exists():
            raise FileNotFoundError(f"Asset not found: {asset_path}")

        suffix = asset_path_obj.suffix.lower()
        is_image = suffix in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        is_video = suffix in (".mp4", ".avi", ".mov", ".mkv", ".webm")

        if not (is_image or is_video):
            raise ValueError(f"Unsupported file type: {suffix}")

        logger.info(f"Scoring saliency: {asset_path_obj.name}")
        t_start = time.time()

        # Extract frames
        if is_video:
            frames = extract_frames(str(asset_path_obj), n_frames=self.n_frames)
        else:
            frames = extract_image_frames(str(asset_path_obj), n_frames=self.n_frames)

        original_size = frames[0].shape[:2]  # (H, W)

        # Preprocess
        clip = preprocess_frames(frames, target_size=(224, 384))
        logger.info(f"Clip tensor shape: {clip.shape}")

        # Load model + run inference
        model = self._ensure_model()

        # Run per-frame saliency (sliding window, same as ViNet paper)
        saliency_maps = []
        clip_size = self.n_frames

        with torch.inference_mode():
            for i in range(len(frames)):
                # Build clip centered on frame i
                start = max(0, i - clip_size // 2)
                end   = min(len(frames), start + clip_size)
                start = max(0, end - clip_size)

                frame_clip = preprocess_frames(
                    frames[start:end], target_size=(224, 384)
                ).to(self.device)

                sal = run_saliency(model, frame_clip, device=self.device,
                                   original_size=original_size)
                saliency_maps.append(sal)

        elapsed = time.time() - t_start
        logger.info(f"Saliency inference complete in {elapsed:.1f}s")

        # Mean saliency map
        mean_sal = np.mean(saliency_maps, axis=0)

        # ROI scores
        roi_scores = {}
        if rois:
            for roi_name, bbox in rois.items():
                roi_scores[roi_name] = score_roi(mean_sal, bbox)
                logger.info(f"ROI '{roi_name}': {roi_scores[roi_name]:.3f}")

        # Global attention metrics
        # Center bias: how much attention is in center 50% of frame?
        h, w = mean_sal.shape
        cy1, cy2 = h // 4, 3 * h // 4
        cx1, cx2 = w // 4, 3 * w // 4
        center_attention = float(mean_sal[cy1:cy2, cx1:cx2].mean())
        peripheral_attention = float(np.concatenate([
            mean_sal[:cy1].flatten(), mean_sal[cy2:].flatten(),
            mean_sal[cy1:cy2, :cx1].flatten(), mean_sal[cy1:cy2, cx2:].flatten()
        ]).mean() + 1e-8)
        center_bias = min(center_attention / peripheral_attention, 1.0)

        # Temporal variance — how much does attention shift over time?
        temporal_variance = float(np.std([m.mean() for m in saliency_maps]) / (np.mean([m.mean() for m in saliency_maps]) + 1e-8))

        # Save outputs
        output_paths = {}
        if save_outputs:
            scores_dir = asset_path_obj.parent.parent / "scores"
            output_paths = save_saliency_outputs(
                frames=frames,
                saliency_maps=saliency_maps,
                output_dir=scores_dir,
                asset_stem=asset_path_obj.stem,
                rois=rois,
            )

        result = {
            "asset_path":          str(asset_path),
            "asset_type":          "image" if is_image else "video",
            # ROI scores (0-1)
            "product_attention":   roi_scores.get("product", 0.0),
            "brand_attention":     roi_scores.get("logo", roi_scores.get("brand", 0.0)),
            "cta_attention":       roi_scores.get("cta", 0.0),
            "roi_scores":          roi_scores,
            # Global metrics
            "center_bias":         center_bias,
            "temporal_variance":   temporal_variance,
            "mean_saliency":       float(mean_sal.mean()),
            # Paths
            "saliency_map_path":   output_paths.get("mean_saliency_npy"),
            "heatmap_png_path":    output_paths.get("heatmap_png"),
            "overlay_png_path":    output_paths.get("overlay_representative"),
            "inference_time_s":    round(elapsed, 1),
        }

        # Unload model to free GPU memory for next scorer
        self.unload()

        return result

    def score_campaign(
        self,
        campaign_dir: str,
        rois: dict[str, tuple[int, int, int, int]] | None = None,
        extensions: tuple[str, ...] = (".mp4", ".avi", ".mov", ".jpg", ".jpeg", ".png"),
    ) -> list[dict]:
        """Score all assets in a campaign's assets/ folder."""
        campaign_path = Path(campaign_dir)
        assets_dir    = campaign_path / "assets"

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

            try:
                result = self.score_asset(str(asset), rois=rois)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to score {asset.name}: {e}")
                results.append({"asset_path": str(asset), "error": str(e)})

            # Save interim results
            scores_dir = campaign_path / "scores"
            scores_dir.mkdir(parents=True, exist_ok=True)
            interim_path = scores_dir / "saliency_scores_interim.json"
            with open(interim_path, "w") as f:
                json.dump(results, f, indent=2)

        # Save final
        final_path = campaign_path / "scores" / "saliency_scores.json"
        with open(final_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saliency scoring complete. Results: {final_path}")
        return results

    def unload(self) -> None:
        """Unload model from GPU memory."""
        if self._model is not None:
            try:
                self._model.cpu()
            except Exception:
                pass
            del self._model
            self._model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            logger.info("SaliencyScorer unloaded")

    def __del__(self):
        self.unload()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ViNet-S Saliency Scorer")
    parser.add_argument("asset_path", help="Path to video or image")
    parser.add_argument("--checkpoint", "-c", help="Path to ViNet-S checkpoint .pt")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--frames", "-f", type=int, default=32,
                        help="Number of frames to sample (default: 32)")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--roi", action="append", metavar="NAME:x1,y1,x2,y2",
                        help="ROI bounding box, e.g. --roi product:100,200,400,500")
    args = parser.parse_args()

    # Parse ROIs
    rois = {}
    if args.roi:
        for roi_str in args.roi:
            name, coords = roi_str.split(":")
            x1, y1, x2, y2 = map(int, coords.split(","))
            rois[name] = (x1, y1, x2, y2)

    scorer = SaliencyScorer(
        checkpoint_path=args.checkpoint,
        device=args.device,
        n_frames=args.frames,
    )

    result = scorer.score_asset(args.asset_path, rois=rois or None)

    output_json = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Saved to {args.output}")
    else:
        print(output_json)
