#!/usr/bin/env python3
"""CLI entry point for the neuro pipeline."""

import argparse
import json
import sys
from pathlib import Path

from .image_analyzer import ImageAnalyzer
from .neural_scorer import NeuralScorer


def run_pipeline(image_path: str) -> dict:
    """
    Run the full neuro pipeline on an image.

    Args:
        image_path: Path to the image file.

    Returns:
        Dictionary containing analysis and scoring results.
    """
    # Run image analysis
    analyzer = ImageAnalyzer(image_path)
    analysis_results = analyzer.analyze()

    # Run neural scoring
    scorer = NeuralScorer()
    neuro_score = scorer.score(analysis_results)

    # Combine results
    results = {
        'image_path': image_path,
        'analysis': {
            'width': analysis_results['width'],
            'height': analysis_results['height'],
            'dimensions': list(analysis_results['dimensions']),
            'brightness_score': analysis_results['brightness_score']
        },
        'scores': {
            'attention_score': neuro_score.attention_score,
            'emotional_valence': neuro_score.emotional_valence,
            'brightness_score': neuro_score.brightness_score,
            'color_variance': neuro_score.color_variance
        }
    }

    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run neuro pipeline on an image for analysis and scoring.'
    )
    parser.add_argument(
        'image_path',
        type=str,
        help='Path to the image file to analyze.'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default=None,
        help='Output file path for JSON results. If not specified, prints to stdout.'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output.'
    )

    args = parser.parse_args()

    # Validate image path
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Image file not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    if not image_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
        print(f"Error: Unsupported image format: {image_path.suffix}", file=sys.stderr)
        sys.exit(1)

    try:
        # Run pipeline
        results = run_pipeline(str(image_path))

        # Output results
        output_json = json.dumps(results, indent=2)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(output_json)
            if args.verbose:
                print(f"Results saved to: {args.output}")
        else:
            print(output_json)

        if args.verbose:
            print(f"\nAnalysis complete for: {args.image_path}")

    except Exception as e:
        print(f"Error processing image: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
