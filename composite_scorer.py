"""Composite Scorer — kombiniert alle Einzel-Scores zu einem Gesamt-Score."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from tribe_scorer import TribeScores
from clip_scorer import ClipScores


WEIGHTS = {
    'neural_engagement':  0.30,
    'emotional_impact':   0.20,
    'visual_attention':   0.20,  # Placeholder bis Saliency da ist
    'brand_consistency':  0.15,
    'social_sentiment':   0.15,  # Placeholder bis MiroFish da ist
}


@dataclass
class CompositeScores:
    asset_path: str
    total_score: float
    neural_engagement: float
    emotional_impact: float
    face_response: float
    motion_response: float
    brand_consistency: float
    top_clip_label: str
    temporal_peak: float
    grade: str  # A/B/C/D


def _grade(score: float) -> str:
    if score >= 0.70: return "A"
    if score >= 0.50: return "B"
    if score >= 0.30: return "C"
    return "D"


def combine(tribe: TribeScores, clip: ClipScores,
            saliency_score: float = 0.5,
            mirofish_sentiment: float = 0.5,
            output_dir: Optional[str] = None) -> CompositeScores:
    """
    Kombiniert TRIBE v2 + CLIP + optionale Saliency/MiroFish Scores.
    Saliency und MiroFish default auf 0.5 (neutral) wenn nicht verfügbar.
    """
    total = (
        tribe.neural_engagement  * WEIGHTS['neural_engagement'] +
        tribe.emotional_impact   * WEIGHTS['emotional_impact'] +
        saliency_score           * WEIGHTS['visual_attention'] +
        clip.brand_match_score   * WEIGHTS['brand_consistency'] +
        mirofish_sentiment       * WEIGHTS['social_sentiment']
    )
    total = round(total, 4)

    scores = CompositeScores(
        asset_path=tribe.asset_path,
        total_score=total,
        neural_engagement=tribe.neural_engagement,
        emotional_impact=tribe.emotional_impact,
        face_response=tribe.face_response,
        motion_response=tribe.motion_response,
        brand_consistency=clip.brand_match_score,
        top_clip_label=clip.top_label,
        temporal_peak=tribe.temporal_peak,
        grade=_grade(total),
    )

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        name = Path(tribe.asset_path).stem
        path = out / f"{name}_composite.json"
        with open(path, "w") as f:
            json.dump(asdict(scores), f, indent=2)
        print(f"Composite saved: {path}")

    return scores
