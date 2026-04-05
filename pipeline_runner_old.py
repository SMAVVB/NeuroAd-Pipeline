"""Pipeline Runner — orchestriert alle Scorer für eine Kampagne."""

import json
from pathlib import Path
from typing import Optional

import tribe_scorer
import clip_scorer
import composite_scorer

SUPPORTED_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".webm",
                         ".jpg", ".jpeg", ".png", ".webp"]

DEFAULT_BRAND_LABELS = [
    "high quality product",
    "emotional advertisement",
    "brand storytelling",
    "call to action",
    "product showcase",
]


def collect_assets(campaign_dir: str) -> list[str]:
    assets_dir = Path(campaign_dir) / "assets"
    if not assets_dir.exists():
        raise FileNotFoundError(f"Assets directory not found: {assets_dir}")
    assets = [str(f) for f in assets_dir.iterdir()
              if f.suffix.lower() in SUPPORTED_EXTENSIONS]
    print(f"Found {len(assets)} assets in {assets_dir}")
    return sorted(assets)


def run_pipeline_a(campaign_dir: str,
                   brand_labels: Optional[list[str]] = None) -> list[dict]:
    """
    Führt Pipeline A auf einem Kampagnen-Ordner durch.

    Args:
        campaign_dir: Pfad zum Kampagnen-Ordner (mit assets/ Unterordner)
        brand_labels: CLIP Brand Labels (optional)

    Returns:
        Liste von Composite-Scores, sortiert nach total_score
    """
    campaign_dir = Path(campaign_dir)
    scores_dir = campaign_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)

    labels = brand_labels or DEFAULT_BRAND_LABELS
    assets = collect_assets(str(campaign_dir))

    if not assets:
        print("No assets found — add videos/images to the assets/ folder.")
        return []

    results = []

    for i, asset_path in enumerate(assets, 1):
        name = Path(asset_path).name
        print(f"\n[{i}/{len(assets)}] Processing: {name}")
        print("-" * 50)

        try:
            # TRIBE v2
            print("  → TRIBE v2 scoring...")
            tribe = tribe_scorer.score(asset_path, output_dir=str(scores_dir))
            print(f"     Neural engagement: {tribe.neural_engagement:.4f}")

            # CLIP
            print("  → CLIP scoring...")
            clip = clip_scorer.score(asset_path, brand_labels=labels,
                                     output_dir=str(scores_dir))
            print(f"     Brand match: {clip.brand_match_score:.4f}")

            # Composite
            composite = composite_scorer.combine(
                tribe, clip, output_dir=str(scores_dir)
            )
            print(f"  ✓ Total score: {composite.total_score:.4f} (Grade: {composite.grade})")

            results.append({
                "asset": name,
                "total_score": composite.total_score,
                "grade": composite.grade,
                "neural_engagement": tribe.neural_engagement,
                "emotional_impact": tribe.emotional_impact,
                "brand_consistency": clip.brand_match_score,
                "top_label": clip.top_label,
                "temporal_peak": tribe.temporal_peak,
            })

        except Exception as e:
            print(f"  ✗ Error processing {name}: {e}")
            continue

    # Sortieren nach total_score
    results.sort(key=lambda x: x["total_score"], reverse=True)

    # Summary speichern
    summary_path = campaign_dir / "scores" / "pipeline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    # Ranking ausgeben
    print("\n" + "=" * 50)
    print("CREATIVE RANKING")
    print("=" * 50)
    for rank, r in enumerate(results, 1):
        print(f"  #{rank} {r['asset']}")
        print(f"      Score: {r['total_score']:.4f}  Grade: {r['grade']}")
        print(f"      Neural: {r['neural_engagement']:.4f}  "
              f"Brand: {r['brand_consistency']:.4f}  "
              f"Peak: {r['temporal_peak']:.0f}s")

    print(f"\nSummary saved: {summary_path}")
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pipeline_runner.py <campaign_dir> [label1,label2,...]")
        sys.exit(1)

    campaign = sys.argv[1]
    labels = sys.argv[2].split(",") if len(sys.argv) > 2 else None

    run_pipeline_a(campaign, brand_labels=labels)
