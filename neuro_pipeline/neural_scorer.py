"""Neural scoring module for image analysis results."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class NeuroScore:
    """Container for neural scoring results."""
    attention_score: float  # 0-1
    emotional_valence: float  # -1 to 1
    brightness_score: float
    color_variance: float


class NeuralScorer:
    """Calculates neural scores based on image analysis metrics."""

    def __init__(self):
        """Initialize the neural scorer."""
        pass

    def calculate_color_variance(self, color_histogram: Dict[str, list[int]]) -> float:
        """
        Calculate color variance from histogram data.

        Returns a normalized variance score (0-1).
        """
        total_variance = 0.0

        for channel_name, channel_data in color_histogram.items():
            # Calculate mean
            total = sum(i * val for i, val in enumerate(channel_data))
            total_pixels = sum(channel_data)
            if total_pixels == 0:
                continue
            mean = total / total_pixels

            # Calculate variance
            variance = sum(((i - mean) ** 2) * val for i, val in enumerate(channel_data))
            variance = variance / total_pixels

            total_variance += variance

        # Normalize variance (max expected variance ~65000 for RGB)
        normalized = min(total_variance / 65000.0, 1.0)
        return round(normalized, 4)

    def calculate_attention_score(self, brightness_score: float, color_variance: float) -> float:
        """
        Calculate attention score based on brightness and color variance.

        Returns a score between 0-1.
        Images with moderate brightness and high variance tend to attract more attention.
        """
        # Optimal brightness for attention is around 0.5-0.7
        brightness_factor = 1.0 - abs(brightness_score - 0.6)

        # Higher variance attracts more attention
        variance_factor = color_variance

        # Combined score with weighted factors
        score = 0.5 * brightness_factor + 0.5 * variance_factor
        return round(max(0.0, min(1.0, score)), 4)

    def calculate_emotional_valence(self, color_histogram: Dict[str, list[int]]) -> float:
        """
        Calculate emotional valence based on color temperature.

        Returns a score between -1 (cool) to 1 (warm).
        """
        red_total = sum(i * val for i, val in enumerate(color_histogram['red']))
        green_total = sum(i * val for i, val in enumerate(color_histogram['green']))
        blue_total = sum(i * val for i, val in enumerate(color_histogram['blue']))

        red_pixels = sum(color_histogram['red'])
        green_pixels = sum(color_histogram['green'])
        blue_pixels = sum(color_histogram['blue'])

        if red_pixels == 0 or green_pixels == 0 or blue_pixels == 0:
            return 0.0

        red_mean = red_total / red_pixels
        green_mean = green_total / green_pixels
        blue_mean = blue_total / blue_pixels

        # Color temperature heuristic:
        # Warm colors: high red, low blue
        # Cool colors: low red, high blue
        # Neutral: balanced

        # Calculate warmth ratio
        warmth_ratio = (red_mean - blue_mean) / 255.0

        # Normalize to -1 to 1 range
        # Warm colors (red > blue) -> positive
        # Cool colors (blue > red) -> negative
        valence = max(-1.0, min(1.0, warmth_ratio))
        return round(valence, 4)

    def score(self, analysis_results: Dict[str, Any]) -> NeuroScore:
        """
        Calculate all neural scores from image analysis results.

        Args:
            analysis_results: Dictionary from ImageAnalyzer.analyze()

        Returns:
            NeuroScore dataclass with all calculated scores.
        """
        brightness_score = analysis_results['brightness_score']
        color_variance = self.calculate_color_variance(analysis_results['color_histogram'])
        attention_score = self.calculate_attention_score(brightness_score, color_variance)
        emotional_valence = self.calculate_emotional_valence(analysis_results['color_histogram'])

        return NeuroScore(
            attention_score=attention_score,
            emotional_valence=emotional_valence,
            brightness_score=brightness_score,
            color_variance=color_variance
        )
