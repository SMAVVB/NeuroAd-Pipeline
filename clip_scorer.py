"""CLIP Brand Consistency Scorer."""

import json
import torch
import clip
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from PIL import Image


@dataclass
class ClipScores:
    """CLIP Scores pro Creative."""
    asset_path: str
    brand_match_score: float      # 0-1, Cosine Similarity zum Brand-Profil
    top_label: str                # Bestes passendes Label
    top_label_score: float        # Score des besten Labels
    all_scores: dict              # Alle Label-Scores


def score(asset_path: str,
          brand_labels: list[str],
          output_dir: Optional[str] = None) -> ClipScores:
    """
    Berechnet CLIP Brand Consistency Score.

    Args:
        asset_path: Pfad zum Bild oder Video-Frame
        brand_labels: Liste von Brand-Beschreibungen z.B.
                      ["luxury car", "sporty", "premium quality"]
        output_dir: Ordner für JSON-Output (optional)

    Returns:
        ClipScores Dataclass
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)

    asset_path = str(asset_path)
    suffix = Path(asset_path).suffix.lower()

    # Bei Video: ersten Frame extrahieren
    if suffix in [".mp4", ".avi", ".mov", ".mkw", ".webm"]:
        import cv2
        cap = cv2.VideoCapture(asset_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise ValueError(f"Cannot read video frame: {asset_path}")
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
    else:
        image = Image.open(asset_path).convert("RGB")

    # CLIP Inferenz
    image_input = preprocess(image).unsqueeze(0).to(device)
    text_inputs = clip.tokenize(brand_labels).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image_input)
        text_features = model.encode_text(text_inputs)

        # Cosine Similarity
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        similarities = (image_features @ text_features.T).squeeze(0)
        probs = similarities.softmax(dim=-1).cpu().numpy()

    all_scores = {label: round(float(prob), 4)
                  for label, prob in zip(brand_labels, probs)}
    top_idx = int(probs.argmax())
    brand_match_score = round(float(probs.mean()), 4)

    scores = ClipScores(
        asset_path=asset_path,
        brand_match_score=brand_match_score,
        top_label=brand_labels[top_idx],
        top_label_score=round(float(probs[top_idx]), 4),
        all_scores=all_scores,
    )

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        asset_name = Path(asset_path).stem
        output_path = output_dir / f"{asset_name}_clip_scores.json"
        with open(output_path, "w") as f:
            json.dump(asdict(scores), f, indent=2)
        print(f"Scores saved: {output_path}")

    return scores


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python clip_scorer.py <asset_path> [label1,label2,...]")
        sys.exit(1)

    asset = sys.argv[1]
    if len(sys.argv) > 2:
        labels = sys.argv[2].split(",")
    else:
        labels = ["epic fantasy adventure", "animated film",
                  "action scene", "dramatic lighting", "emotional storytelling"]

    result = score(asset, brand_labels=labels)

    print("\n=== CLIP Scores ===")
    print(f"Brand Match Score:  {result.brand_match_score:.4f}")
    print(f"Top Label:          {result.top_label} ({result.top_label_score:.4f})")
    print("\nAll scores:")
    for label, s in sorted(result.all_scores.items(), key=lambda x: -x[1]):
        print(f"  {s:.4f}  {label}")
