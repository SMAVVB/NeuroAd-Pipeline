#!/usr/bin/env python3
"""Test script that downloads a sample image and runs the full pipeline."""

import sys
import urllib.request
from pathlib import Path

from .image_analyzer import ImageAnalyzer
from .neural_scorer import NeuralScorer


def download_sample_image(output_dir: str = ".") -> str:
    """
    Download a sample image from the web.

    Uses a placeholder image from picsum.photos.

    Args:
        output_dir: Directory to save the downloaded image.

    Returns:
        Path to the downloaded image file.
    """
    sample_url = "https://picsum.photos/800/600"
    output_path = Path(output_dir) / "sample_image.jpg"

    print(f"Downloading sample image from {sample_url}...")
    urllib.request.urlretrieve(sample_url, output_path)
    print(f"Downloaded: {output_path}")

    return str(output_path)


def run_test_pipeline(image_path: str) -> None:
    """
    Run the full neuro pipeline on an image and print results.

    Args:
        image_path: Path to the image file.
    """
    print("\n" + "=" * 50)
    print("NEURO PIPELINE - TEST RUN")
    print("=" * 50)

    # Run image analysis
    print("\n[1/2] Analyzing image...")
    analyzer = ImageAnalyzer(image_path)
    analysis = analyzer.analyze()

    print(f"  Dimensions: {analysis['dimensions'][0]} x {analysis['dimensions'][1]}")
    print(f"  Brightness Score: {analysis['brightness_score']:.4f}")

    # Run neural scoring
    print("\n[2/2] Calculating neural scores...")
    scorer = NeuralScorer()
    scores = scorer.score(analysis)

    print("\n" + "-" * 50)
    print("RESULTS")
    print("-" * 50)
    print(f"\n  Attention Score:   {scores.attention_score:.4f}  (0-1, higher = more attention-grabbing)")
    print(f"  Emotional Valence: {scores.emotional_valence:.4f}  (-1 to 1, negative=cool, positive=warm)")
    print(f"  Brightness Score:  {scores.brightness_score:.4f}")
    print(f"  Color Variance:    {scores.color_variance:.4f}")

    # Interpret results
    print("\n" + "-" * 50)
    print("INTERPRETATION")
    print("-" * 50)

    # Attention interpretation
    if scores.attention_score >= 0.7:
        attention_desc = "High attention potential - likely to stand out"
    elif scores.attention_score >= 0.4:
        attention_desc = "Moderate attention potential"
    else:
        attention_desc = "Low attention potential - may blend in"

    print(f"\n  Attention: {attention_desc}")

    # Emotional valence interpretation
    if scores.emotional_valence >= 0.3:
        emotion_desc = "Warm/positive tone (red/orange dominant)"
    elif scores.emotional_valence <= -0.3:
        emotion_desc = "Cool/calm tone (blue dominant)"
    else:
        emotion_desc = "Neutral/balanced tone"

    print(f"  Emotion:   {emotion_desc}")

    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50 + "\n")


def main():
    """Main entry point for test script."""
    try:
        # Download sample image
        image_path = download_sample_image()

        # Run pipeline
        run_test_pipeline(image_path)

    except urllib.error.URLError as e:
        print(f"Error downloading image: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running pipeline: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
