#!/usr/bin/env python3
"""
verify_fallback.py — Verify that MiroFish runtime error returns fallback scores.

Mocks a failing MiroFish simulation (RuntimeError with "No entities matching criteria")
and asserts that the fallback dictionary is returned instead of crashing.

Usage:
    python verify_fallback.py
    # Exit code must be 0
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline_runner import run_mirofish


class TestMiroFishFallback(unittest.TestCase):
    """Tests for the MiroFish fallback mechanism."""

    def test_runtime_error_returns_fallback(self):
        """When run_simulation raises RuntimeError, fallback dict is returned."""
        mock_client = MagicMock()
        mock_client.run_simulation.side_effect = RuntimeError(
            "Simulation Start failed: No entities matching criteria found"
        )

        with patch("pipeline_runner.MiroFishClient", return_value=mock_client):
            result = run_mirofish(
                assets=[Path("/tmp/fake.mp4")],
                config={},
                campaign_dir=Path("/tmp"),
                brand_context="test campaign",
            )

        # Assert fallback keys are present
        self.assertEqual(result["positive_sentiment"], 0.5)
        self.assertEqual(result["negative_sentiment"], 0.5)
        self.assertEqual(result["virality_score"], 0.5)
        self.assertEqual(result["controversy_risk"], 0.5)
        self.assertEqual(result["social_score"], 0.5)
        self.assertEqual(result["source"], "fallback")
        self.assertIn("No entities matching criteria", result["note"])

    def test_generic_exception_returns_error_fallback(self):
        """When run_simulation raises a non-RuntimeError, source='error' is returned."""
        mock_client = MagicMock()
        mock_client.run_simulation.side_effect = ConnectionError("port unreachable")

        with patch("pipeline_runner.MiroFishClient", return_value=mock_client):
            result = run_mirofish(
                assets=[Path("/tmp/fake.mp4")],
                config={},
                campaign_dir=Path("/tmp"),
                brand_context="test campaign",
            )

        self.assertEqual(result["positive_sentiment"], 0.5)
        self.assertEqual(result["source"], "error")


if __name__ == "__main__":
    unittest.main()
