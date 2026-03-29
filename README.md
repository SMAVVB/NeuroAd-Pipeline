# Neuro Pipeline

A Python module for image analysis and neural scoring. Extracts visual metrics from images and calculates attention scores and emotional valence based on color analysis.

## Overview

The Neuro Pipeline takes an image and performs the following steps:

1. **Image Analysis** - Extracts dimensions, color histogram (RGB), and brightness score
2. **Neural Scoring** - Calculates:
   - **Attention Score** (0-1): Based on brightness and color variance
   - **Emotional Valence** (-1 to 1): Based on color temperature (warm vs cool)

## Installation

```bash
pip install pillow
```

## Usage

### As a Python Module

```python
from neuro_pipeline import ImageAnalyzer, NeuralScorer

# Analyze an image
analyzer = ImageAnalyzer('path/to/image.jpg')
analysis = analyzer.analyze()

print(f"Dimensions: {analysis['dimensions']}")
print(f"Brightness: {analysis['brightness_score']}")

# Score the image
scorer = NeuralScorer()
scores = scorer.score(analysis)

print(f"Attention Score: {scores.attention_score}")
print(f"Emotional Valence: {scores.emotional_valence}")
```

### Command Line Interface

```bash
# Run on an image (outputs JSON to stdout)
python -m neuro_pipeline.main path/to/image.jpg

# Save results to a file
python -m neuro_pipeline.main path/to/image.jpg --output results.json

# Verbose mode
python -m neuro_pipeline.main path/to/image.jpg -v
```

## Output Format

The pipeline returns a dictionary with two main sections:

```json
{
  "image_path": "path/to/image.jpg",
  "analysis": {
    "width": 1920,
    "height": 1080,
    "dimensions": [1920, 1080],
    "brightness_score": 0.45
  },
  "scores": {
    "attention_score": 0.72,
    "emotional_valence": 0.34,
    "brightness_score": 0.45,
    "color_variance": 0.68
  }
}
```

## Classes

### ImageAnalyzer

Analyzes images and extracts visual metrics.

- `__init__(image_path)`: Initialize with image path
- `analyze()`: Run full analysis, returns dict with metrics

### NeuralScorer

Calculates neural scores from analysis results.

- `__init__()`: Initialize scorer
- `score(analysis_results)`: Calculate scores, returns `NeuroScore` dataclass

### NeuroScore

Dataclass containing:
- `attention_score`: 0-1 (higher = more attention-grabbing)
- `emotional_valence`: -1 to 1 (negative = cool, positive = warm)
- `brightness_score`: 0-1
- `color_variance`: 0-1

## Color Temperature Heuristics

- **Warm colors** (red/orange dominant): Positive valence
- **Cool colors** (blue dominant): Negative valence
- **Neutral colors**: Valence near 0

## License

MIT
