"""CLIP Scorer Module wrapper for the BaseScorerModule interface."""

import gc
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
import torch
from PIL import Image

from tools.base_scorer import BaseScorerModule


class CLIPScorerModule(BaseScorerModule):
    """
    Wrapper for CLIP brand consistency scoring.

    This class wraps the existing CLIP scoring functionality to conform
    to the BaseScorerModule interface, enabling easy replacement with
    newer models like SigLIP2.

    Usage:
        from tools.clip_scorer_wrapper import CLIPScorerModule

        scorer = CLIPScorerModule(name="CLIP", version="ViT-B/32")
        result = scorer.score(
            asset_path="path/to/asset.jpg",
            brand_context={"brand_labels": ["sporty", "premium", "innovative"]}
        )
    """

    def __init__(self, name: str = "CLIP", version: str = "ViT-B/32") -> None:
        """
        Initialize the CLIP scorer module.

        Args:
            name: Module name (default: "CLIP")
            version: Model version string (default: "ViT-B/32")
        """
        super().__init__(name=name, version=version)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.preprocess = None
        self._loaded = False

    def _load_model(self) -> None:
        """Load CLIP model and preprocess (lazy initialization)."""
        if self._loaded:
            return

        import clip as clip_lib

        self.model, self.preprocess = clip_lib.load(
            self.version, device=self.device
        )
        self._loaded = True

    def score(self, asset_path: str, brand_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score an asset using CLIP brand consistency.

        Args:
            asset_path: Path to the media file (image or video)
            brand_context: Dictionary with "brand_labels" key containing
                          list of brand description strings

        Returns:
            Dictionary with CLIP scores including:
                - brand_match_score: Average similarity to brand labels
                - top_label: Best matching label
                - top_label_score: Score of best matching label
                - all_scores: Dictionary of all label scores
        """
        self._load_model()

        brand_labels = brand_context.get(
            "brand_labels", ["advertisement", "product", "brand"]
        )

        VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        suffix = str(Path(asset_path).suffix.lower())

        # Extract representative frames
        if suffix in VIDEO_EXTENSIONS:
            cap = cv2.VideoCapture(asset_path)
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
            img = cv2.imread(asset_path)
            frames = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB)] if img is not None else []

        if not frames:
            return {
                "asset_path": asset_path,
                "error": "No frames extracted from asset",
            }

        # CLIP inference on each frame
        text_tokens = torch.cat(
            [clip_lib.tokenize(label) for label in brand_labels]
        ).to(self.device)

        all_scores: Dict[str, list] = {label: [] for label in brand_labels}

        with torch.inference_mode():
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(
                dim=-1, keepdim=True
            )

            for frame_rgb in frames:
                pil_img = Image.fromarray(frame_rgb)
                image_input = self.preprocess(pil_img).unsqueeze(0).to(self.device)
                image_features = self.model.encode_image(image_input)
                image_features = image_features / image_features.norm(
                    dim=-1, keepdim=True
                )

                similarities = (image_features @ text_features.T).squeeze(0)
                probs = similarities.softmax(dim=-1).cpu().numpy()

                for label, prob in zip(brand_labels, probs):
                    all_scores[label].append(float(prob))

        # Average across frames
        avg_scores = {
            label: float(np.mean(scores))
            for label, scores in all_scores.items()
        }
        top_label = max(avg_scores, key=avg_scores.get)
        brand_match = float(np.mean(list(avg_scores.values())))

        return {
            "asset_path": asset_path,
            "brand_match_score": brand_match,
            "top_label": top_label,
            "top_label_score": avg_scores[top_label],
            "all_scores": avg_scores,
        }

    def is_available(self) -> bool:
        """
        Check if CLIP is available for scoring.

        Returns:
            True if the clip library and model can be loaded
        """
        try:
            import clip as clip_lib
            return True
        except ImportError:
            return False

    def unload(self) -> None:
        """Unload the CLIP model from GPU memory."""
        if self.model is not None:
            del self.model
            self.model = None
        self._loaded = False

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
