"""Image analysis module using PIL."""

from dataclasses import dataclass
from PIL import Image
from typing import Dict, Any


@dataclass
class ImageMetrics:
    """Container for image analysis metrics."""
    width: int
    height: int
    dimensions: tuple[int, int]
    color_histogram: Dict[str, list[int]]
    brightness_score: float


class ImageAnalyzer:
    """Analyzes images and extracts metrics."""

    def __init__(self, image_path: str):
        """
        Initialize the analyzer with an image path.

        Args:
            image_path: Path to the image file to analyze.
        """
        self.image_path = image_path
        self.image = None

    def load_image(self) -> None:
        """Load the image using PIL."""
        self.image = Image.open(self.image_path)

    def get_dimensions(self) -> tuple[int, int]:
        """Get image dimensions as (width, height)."""
        if self.image is None:
            self.load_image()
        return self.image.size

    def get_color_histogram(self) -> Dict[str, list[int]]:
        """Extract RGB color histogram from the image."""
        if self.image is None:
            self.load_image()

        # Convert to RGB if necessary
        if self.image.mode != 'RGB':
            rgb_image = self.image.convert('RGB')
        else:
            rgb_image = self.image

        # Get histogram (256 bins per channel)
        histogram = rgb_image.histogram()

        # Split into R, G, B channels
        red = histogram[0:256]
        green = histogram[256:512]
        blue = histogram[512:768]

        return {
            'red': red,
            'green': green,
            'blue': blue
        }

    def get_brightness_score(self) -> float:
        """
        Calculate brightness score (0-1).

        Based on average luminance of the image.
        """
        if self.image is None:
            self.load_image()

        # Convert to grayscale for luminance calculation
        gray = self.image.convert('L')
        pixels = list(gray.getdata())

        if not pixels:
            return 0.0

        avg_luminance = sum(pixels) / len(pixels)
        # Normalize to 0-1 range
        return avg_luminance / 255.0

    def analyze(self) -> Dict[str, Any]:
        """
        Run full analysis and return all metrics.

        Returns:
            Dictionary containing all image metrics.
        """
        dimensions = self.get_dimensions()

        return {
            'width': dimensions[0],
            'height': dimensions[1],
            'dimensions': dimensions,
            'color_histogram': self.get_color_histogram(),
            'brightness_score': self.get_brightness_score()
        }
