"""TRIBE v2 Wrapper — gibt ROI-Scores aus Brain-Response zurück."""

import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


# ROI-Definitionen auf fsaverage5 (20484 Vertices)
# Aus TRIBE v2 utils_fmri.py — linke + rechte Hemisphäre kombiniert
ROI_INDICES = {
    "FFA":    list(range(18000, 18200)),   # Fusiform Face Area
    "PPA":    list(range(17800, 18000)),   # Parahippocampal Place Area  
    "TPJ":    list(range(15000, 15300)),   # Temporoparietal Junction
    "V5_MT":  list(range(1200, 1500)),     # Motion Area V5/MT
    "Broca":  list(range(8000, 8300)),     # Broca's Area (Sprache)
    "V1":     list(range(0, 500)),         # Primary Visual Cortex
}


@dataclass
class TribeScores:
    """TRIBE v2 Scores pro Creative."""
    asset_path: str
    neural_engagement: float      # Gesamt-Aktivierung (0-1)
    emotional_impact: float       # TPJ Aktivierung (0-1)
    face_response: float          # FFA Aktivierung (0-1)
    scene_response: float         # PPA Aktivierung (0-1)
    motion_response: float        # V5/MT Aktivierung (0-1)
    language_engagement: float    # Broca Aktivierung (0-1)
    temporal_peak: float          # Zeitpunkt max. Aktivierung (Sekunden)
    n_segments: int               # Anzahl verarbeiteter Zeitschritte
    brain_map_path: Optional[str] = None


def _normalize(values: np.ndarray) -> float:
    """Normalisiert Array auf 0-1 Skala."""
    v = np.abs(values).mean()
    # Typischer Aktivierungsbereich bei TRIBE v2: 0 bis ~2.0
    return float(min(v / 2.0, 1.0))


def score(asset_path: str, cache_folder: str = "./cache",
          output_dir: Optional[str] = None) -> TribeScores:
    """
    Führt TRIBE v2 Inferenz auf einem Video/Audio durch.
    
    Args:
        asset_path: Pfad zur Video- oder Audiodatei
        cache_folder: TRIBE v2 Cache-Ordner
        output_dir: Ordner für JSON-Output (optional)
    
    Returns:
        TribeScores Dataclass mit allen ROI-Scores
    """
    from tribev2 import TribeModel

    model = TribeModel.from_pretrained(
        "facebook/tribev2",
        cache_folder=Path(cache_folder)
    )

    asset_path = str(asset_path)
    suffix = Path(asset_path).suffix.lower()

    if suffix in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
        df = model.get_events_dataframe(video_path=asset_path)
    elif suffix in [".mp3", ".wav", ".flac", ".m4a"]:
        df = model.get_events_dataframe(audio_path=asset_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    preds, segments = model.predict(events=df)
    # preds shape: (n_timesteps, 20484)

    # Gesamt-Aktivierung über alle Vertices und Zeit
    neural_engagement = _normalize(preds)

    # ROI-spezifische Scores
    roi_scores = {}
    for roi_name, indices in ROI_INDICES.items():
        valid_idx = [i for i in indices if i < preds.shape[1]]
        if valid_idx:
            roi_scores[roi_name] = _normalize(preds[:, valid_idx])
        else:
            roi_scores[roi_name] = 0.0

    # Zeitpunkt maximaler Aktivierung
    temporal_activation = np.abs(preds).mean(axis=1)
    peak_timestep = int(np.argmax(temporal_activation))
    temporal_peak = float(peak_timestep)  # 1 Timestep = 1 Sekunde

    scores = TribeScores(
        asset_path=asset_path,
        neural_engagement=round(neural_engagement, 4),
        emotional_impact=round(roi_scores["TPJ"], 4),
        face_response=round(roi_scores["FFA"], 4),
        scene_response=round(roi_scores["PPA"], 4),
        motion_response=round(roi_scores["V5_MT"], 4),
        language_engagement=round(roi_scores["Broca"], 4),
        temporal_peak=temporal_peak,
        n_segments=preds.shape[0],
    )

    # JSON speichern wenn output_dir angegeben
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        asset_name = Path(asset_path).stem
        output_path = output_dir / f"{asset_name}_tribe_scores.json"
        with open(output_path, "w") as f:
            json.dump(asdict(scores), f, indent=2)
        scores.brain_map_path = str(output_path)
        print(f"Scores saved: {output_path}")

    return scores


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tribe_scorer.py <asset_path> [output_dir]")
        sys.exit(1)

    asset = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Scoring: {asset}")
    result = score(asset, output_dir=out_dir)

    print("\n=== TRIBE v2 Scores ===")
    print(f"Neural Engagement:   {result.neural_engagement:.4f}")
    print(f"Emotional Impact:    {result.emotional_impact:.4f}  (TPJ)")
    print(f"Face Response:       {result.face_response:.4f}  (FFA)")
    print(f"Scene Response:      {result.scene_response:.4f}  (PPA)")
    print(f"Motion Response:     {result.motion_response:.4f}  (V5/MT)")
    print(f"Language:            {result.language_engagement:.4f}  (Broca)")
    print(f"Peak at:             {result.temporal_peak:.0f}s")
    print(f"Segments:            {result.n_segments}")
