#!/usr/bin/env python3
"""
visualize_brain.py — TRIBE v2 Brain Activity Visualizer

Renders TRIBE v2 predictions (.npy) as 3D brain surface maps using Nilearn.

Usage:
    python visualize_brain.py campaigns/test_campaign/scores/sintel_trailer_tribe_preds.npy
    python visualize_brain.py path/to/preds.npy --output brain_map.png
    python visualize_brain.py path/to/preds.npy --frame 25  # specific timepoint
"""

import argparse
import sys
from pathlib import Path

import numpy as np


def load_preds(preds_path: str) -> np.ndarray:
    """Load TRIBE v2 predictions from .npy file."""
    path = Path(preds_path)
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {path}")
    preds = np.load(path)
    print(f"Loaded predictions: shape={preds.shape}, dtype={preds.dtype}")
    print(f"  Time steps: {preds.shape[0]}")
    print(f"  Vertices:   {preds.shape[1]} (fsaverage5 = 20484)")
    return preds


def compute_stat_map(preds: np.ndarray, mode: str = "mean", frame: int = None) -> np.ndarray:
    """
    Compute a single stat map from predictions.

    Args:
        preds: (n_timesteps, 20484) array
        mode: 'mean' | 'peak' | 'frame'
        frame: specific timepoint index (only used when mode='frame')

    Returns:
        (20484,) array for surface projection
    """
    if mode == "mean":
        stat = np.mean(np.abs(preds), axis=0)
        print(f"Stat map: mean activation across {preds.shape[0]} timepoints")
    elif mode == "peak":
        peak_idx = np.argmax(np.mean(np.abs(preds), axis=1))
        stat = np.abs(preds[peak_idx])
        print(f"Stat map: peak timepoint = {peak_idx}")
    elif mode == "frame":
        if frame is None:
            frame = preds.shape[0] // 2
        frame = min(frame, preds.shape[0] - 1)
        stat = np.abs(preds[frame])
        print(f"Stat map: specific frame = {frame}")
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return stat.astype(np.float32)


def split_hemispheres(stat_map: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Split fsaverage5 stat map into left/right hemispheres.
    fsaverage5: 10242 vertices per hemisphere, total 20484.
    """
    n_vertices_per_hemi = stat_map.shape[0] // 2
    lh = stat_map[:n_vertices_per_hemi]
    rh = stat_map[n_vertices_per_hemi:]
    return lh, rh


def visualize(
    preds_path: str,
    output_path: str = None,
    mode: str = "mean",
    frame: int = None,
    colormap: str = "cold_hot",
    threshold: float = None,
) -> str:
    """
    Main visualization function.

    Args:
        preds_path: Path to .npy predictions file
        output_path: Output PNG path (auto-generated if None)
        mode: 'mean' | 'peak' | 'frame'
        frame: specific timepoint (only for mode='frame')
        colormap: Nilearn colormap
        threshold: threshold for display (auto if None)

    Returns:
        Path to saved PNG
    """
    from nilearn import datasets, plotting, surface

    preds = load_preds(preds_path)
    stat_map = compute_stat_map(preds, mode=mode, frame=frame)
    lh_data, rh_data = split_hemispheres(stat_map)

    print("\nLoading fsaverage5 surface...")
    fsaverage = datasets.fetch_surf_fsaverage(mesh="fsaverage5")

    # Auto threshold at 75th percentile for cleaner visualization
    if threshold is None:
        threshold = float(np.percentile(stat_map, 75))
        print(f"Auto threshold: {threshold:.4f} (75th percentile)")

    # Output path
    if output_path is None:
        preds_path_obj = Path(preds_path)
        output_dir = preds_path_obj.parent
        stem = preds_path_obj.stem.replace("_tribe_preds", "")
        output_path = str(output_dir / f"{stem}_brain_{mode}.png")

    print(f"\nRendering brain surface maps...")
    print(f"Output: {output_path}")

    # Create 4-panel figure: LH lateral, LH medial, RH lateral, RH medial
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), subplot_kw={"projection": "3d"})
    fig.patch.set_facecolor("#1a1a2e")

    title_map = {
        "mean": "Mean Neural Activation",
        "peak": "Peak Neural Activation",
        "frame": f"Neural Activation (frame {frame})",
    }
    asset_name = Path(preds_path).stem.replace("_tribe_preds", "")
    fig.suptitle(
        f"TRIBE v2 — {asset_name}\n{title_map[mode]}",
        color="white",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    views = [
        ("Left Hemisphere — Lateral",  fsaverage.infl_left,  fsaverage.sulc_left,  lh_data, "lateral"),
        ("Left Hemisphere — Medial",   fsaverage.infl_left,  fsaverage.sulc_left,  lh_data, "medial"),
        ("Right Hemisphere — Lateral", fsaverage.infl_right, fsaverage.sulc_right, rh_data, "lateral"),
        ("Right Hemisphere — Medial",  fsaverage.infl_right, fsaverage.sulc_right, rh_data, "medial"),
    ]

    for ax, (title, mesh, bg_map, data, view) in zip(axes.flat, views):
        plotting.plot_surf_stat_map(
            surf_mesh=mesh,
            stat_map=data,
            bg_map=bg_map,
            hemi="left" if "Left" in title else "right",
            view=view,
            colorbar=True,
            cmap=colormap,
            threshold=threshold,
            title=title,
            axes=ax,
            figure=fig,
        )
        ax.set_facecolor("#1a1a2e")
        ax.title.set_color("white")
        ax.title.set_fontsize(9)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close()

    print(f"✓ Saved: {output_path}")
    return output_path


def visualize_temporal(preds_path: str, output_path: str = None) -> str:
    """
    Plot temporal activation profile — how neural response changes over time.
    Useful for seeing which moments in the video drive the most brain activity.
    """
    import matplotlib.pyplot as plt

    preds = load_preds(preds_path)

    # Mean activation per timepoint
    temporal = np.mean(np.abs(preds), axis=1)
    peak_idx = np.argmax(temporal)

    if output_path is None:
        preds_path_obj = Path(preds_path)
        stem = preds_path_obj.stem.replace("_tribe_preds", "")
        output_path = str(preds_path_obj.parent / f"{stem}_temporal.png")

    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    ax.plot(temporal, color="#00d4ff", linewidth=2, label="Mean activation")
    ax.axvline(peak_idx, color="#ff6b6b", linestyle="--", linewidth=1.5,
               label=f"Peak (segment {peak_idx})")
    ax.fill_between(range(len(temporal)), temporal, alpha=0.2, color="#00d4ff")

    ax.set_xlabel("Segment index", color="white")
    ax.set_ylabel("Mean |activation|", color="white")
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    asset_name = Path(preds_path).stem.replace("_tribe_preds", "")
    ax.set_title(f"TRIBE v2 — {asset_name} — Temporal Activation Profile",
                 color="white", fontsize=12)
    ax.legend(facecolor="#2a2a4e", labelcolor="white")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close()

    print(f"✓ Saved temporal plot: {output_path}")
    return output_path


def print_roi_summary(preds_path: str) -> None:
    """Print a text summary of ROI activations."""
    preds = load_preds(preds_path)
    stat_map = compute_stat_map(preds, mode="mean")
    global_max = stat_map.max() + 1e-8

    ROI_RANGES = {
        "TPJ  (Emotional Processing)": (8000,  9500),
        "FFA  (Face Recognition)":     (9500, 10500),
        "PPA  (Scene/Place Area)":     (7000,  8000),
        "V5   (Motion Perception)":    (5500,  6500),
        "Broca (Language/Syntax)":     (2000,  3000),
        "A1   (Auditory Cortex)":      (1000,  2000),
    }

    print("\n" + "="*50)
    print(" ROI Activation Summary")
    print("="*50)
    print(f" Asset: {Path(preds_path).stem.replace('_tribe_preds', '')}")
    print(f" Segments: {preds.shape[0]}, Vertices: {preds.shape[1]}")
    print("-"*50)

    scores = {}
    for roi_name, (start, end) in ROI_RANGES.items():
        score = float(stat_map[start:end].mean() / global_max)
        scores[roi_name] = score

    # Sort by score descending
    for roi_name, score in sorted(scores.items(), key=lambda x: -x[1]):
        bar_len = int(score * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f" {roi_name:35s} {bar} {score:.3f}")

    neural_engagement = float(stat_map.mean() / global_max)
    peak_segment = int(np.argmax(np.mean(np.abs(preds), axis=1)))
    print("-"*50)
    print(f" Neural Engagement (overall): {neural_engagement:.3f}")
    print(f" Peak activation segment:     {peak_segment}")
    print("="*50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize TRIBE v2 brain predictions")
    parser.add_argument("preds_path", help="Path to .npy predictions file")
    parser.add_argument("--output", "-o", help="Output PNG path")
    parser.add_argument("--mode", default="mean",
                        choices=["mean", "peak", "frame"],
                        help="Visualization mode (default: mean)")
    parser.add_argument("--frame", type=int, default=None,
                        help="Specific frame index (only for --mode frame)")
    parser.add_argument("--colormap", default="cold_hot",
                        help="Nilearn colormap (default: cold_hot)")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Display threshold (default: auto 75th percentile)")
    parser.add_argument("--temporal", action="store_true",
                        help="Also generate temporal activation plot")
    parser.add_argument("--summary", action="store_true", default=True,
                        help="Print ROI text summary (default: True)")
    args = parser.parse_args()

    if args.summary:
        print_roi_summary(args.preds_path)

    output = visualize(
        preds_path=args.preds_path,
        output_path=args.output,
        mode=args.mode,
        frame=args.frame,
        colormap=args.colormap,
        threshold=args.threshold,
    )

    if args.temporal:
        visualize_temporal(args.preds_path)

    print(f"\nDone. Open: {output}")
