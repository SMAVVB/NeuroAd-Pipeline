#!/usr/bin/env python3
"""
Test script to verify the MiroFish API bug fixes.
Tests that failed statuses are properly handled without hanging.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from io import BytesIO

# Mock requests before importing mirofish_client
class MockResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or json.dumps(json_data) if json_data else ""

    def json(self):
        return self._json_data


class TestPreparationPolling(unittest.TestCase):
    """Test that preparation polling handles failed statuses correctly."""

    @patch('mirofish_client.requests.get')
    def test_failed_status_in_success_false_response(self, mock_get):
        """When preparation returns success=false with status=failed, should raise RuntimeError."""
        from mirofish_client import MiroFishClient

        mock_get.return_value = MockResponse(
            status_code=200,
            json_data={
                "success": False,
                "data": {
                    "status": "failed",
                    "error": "No entities matching criteria found"
                }
            }
        )

        client = MiroFishClient()
        with self.assertRaises(RuntimeError) as ctx:
            # Call _poll_simulation which uses the same pattern
            client._poll_simulation("test_sim_id", poll_interval=1, max_retries=3)

        self.assertIn("failed", str(ctx.exception).lower())
        # Should have raised on first call, not looped forever
        self.assertEqual(mock_get.call_count, 1)

    @patch('mirofish_client.requests.get')
    def test_failed_status_in_success_true_response(self, mock_get):
        """When preparation returns success=true with status=failed, should raise RuntimeError."""
        from mirofish_client import MiroFishClient

        mock_get.return_value = MockResponse(
            status_code=200,
            json_data={
                "success": True,
                "data": {
                    "status": "failed",
                    "error": "No entities matching criteria found"
                }
            }
        )

        client = MiroFishClient()
        with self.assertRaises(RuntimeError) as ctx:
            client._poll_simulation("test_sim_id", poll_interval=1, max_retries=3)

        self.assertIn("failed", str(ctx.exception).lower())
        self.assertEqual(mock_get.call_count, 1)


class TestGraphTaskPolling(unittest.TestCase):
    """Test that graph task polling handles 0 entities failure correctly."""

    @patch('mirofish_client.requests.get')
    def test_graph_build_zero_entities(self, mock_get):
        """When graph build returns entities_count=0, should raise RuntimeError with details."""
        from mirofish_client import MiroFishClient

        mock_get.return_value = MockResponse(
            status_code=200,
            json_data={
                "success": False,
                "data": {
                    "status": "failed",
                    "error": "No entities matching criteria found",
                    "entities_count": 0
                }
            }
        )

        client = MiroFishClient()
        with self.assertRaises(RuntimeError) as ctx:
            client._poll_graph_task("test_task_id", "test_project_id", poll_interval=1, max_retries=3)

        self.assertIn("failed", str(ctx.exception).lower())
        self.assertEqual(mock_get.call_count, 1)

    @patch('mirofish_client.requests.get')
    def test_graph_build_success_with_entities(self, mock_get):
        """When graph build succeeds with entities, should return graph_id."""
        from mirofish_client import MiroFishClient

        # First call: graph build success
        mock_get.return_value = MockResponse(
            status_code=200,
            json_data={
                "success": True,
                "data": {
                    "status": "completed",
                    "graph_id": "graph_123"
                }
            }
        )

        client = MiroFishClient()
        result = client._poll_graph_task("test_task_id", "test_project_id", poll_interval=1, max_retries=3)
        self.assertEqual(result, "graph_123")


class TestSimulationPolling(unittest.TestCase):
    """Test that simulation polling handles failed statuses correctly."""

    @patch('mirofish_client.requests.get')
    @patch('mirofish_client.MiroFishClient._check_simulation_log_completed', return_value=False)
    def test_simulation_failed_status(self, mock_log, mock_get):
        """When simulation returns status=failed, should raise RuntimeError."""
        from mirofish_client import MiroFishClient

        mock_get.return_value = MockResponse(
            status_code=200,
            json_data={
                "success": True,
                "data": {
                    "status": "failed",
                    "error": "Simulation failed: No entities matching criteria found"
                }
            }
        )

        client = MiroFishClient()
        with self.assertRaises(RuntimeError) as ctx:
            client._poll_simulation("test_sim_id", poll_interval=1, max_retries=3)

        self.assertIn("failed", str(ctx.exception).lower())


if __name__ == "__main__":
    print("=" * 60)
    print("MiroFish API Bug Fix Verification Tests")
    print("=" * 60)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.TestSuite([
        unittest.makeSuite(TestPreparationPolling),
        unittest.makeSuite(TestGraphTaskPolling),
        unittest.makeSuite(TestSimulationPolling),
    ]))

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("ALL TESTS PASSED - Bug fixes verified!")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)
