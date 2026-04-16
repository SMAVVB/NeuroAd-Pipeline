"""Base class for pipeline scorer modules.

This module defines the abstract BaseScorerModule class that all scoring
modules must implement. This enables easy module upgrades (e.g., CLIP to
SigLIP2) by providing a consistent interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseScorerModule(ABC):
    """
    Abstract base class for all pipeline scorer modules.

    Modules implementing this interface can be easily swapped without
    changing the pipeline runner logic.

    Example implementation:
        class CLIPScorerModule(BaseScorerModule):
            def __init__(self, name: str, version: str):
                super().__init__(name, version)
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

            def score(self, asset_path: str, brand_context: dict) -> dict:
                # Implementation here
                return result

            def is_available(self) -> bool:
                return True  # or check if model files exist
    """

    def __init__(self, name: str, version: str) -> None:
        """
        Initialize a scorer module.

        Args:
            name: The name of the scorer (e.g., "CLIP", "SigLIP2", "Emotion")
            version: The version string of the scorer
        """
        self.name = name
        self.version = version

    @abstractmethod
    def score(self, asset_path: str, brand_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score an asset given brand context.

        Args:
            asset_path: Path to the media file (image or video)
            brand_context: Dictionary containing brand labels and context
                          (e.g., {"brand_labels": ["sporty", "premium"]})

        Returns:
            Dictionary with scoring results
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the scorer module is available for use.

        Returns:
            True if the module can run (models loaded, dependencies met),
            False otherwise
        """
        pass

    def unload(self) -> None:
        """
        Unload the module from memory/GPU.

        Override in subclasses to free resources when done.
        """
        pass
