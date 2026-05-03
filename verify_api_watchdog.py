"""Verification script for GET /api/watchdog/status endpoint.

Uses FastAPI TestClient to hit the endpoint and assert correct 200 OK
responses with the expected JSON structure in both the file-exists and
file-missing scenarios.
"""

import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure the API module is importable
SCRIPT_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = SCRIPT_DIR / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

import api.main as api_module

# The real project root (where watchdog_status.json would live)
REAL_PROJECT_ROOT = SCRIPT_DIR


def run():
    client = TestClient(api_module.app)

    status_file = REAL_PROJECT_ROOT / "watchdog_status.json"
    exists_before = status_file.exists()
    backup = None
    if exists_before:
        backup = status_file.read_text()

    # --- Test A: No file → default offline status ---
    if exists_before:
        status_file.unlink()

    response = client.get("/api/watchdog/status")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["current_status"] == "Offline"
    assert data["total_crashes_handled"] == 0
    print("[PASS] Missing watchdog_status.json -> default Offline status")

    # --- Test B: File exists -> return contents ---
    test_status = {
        "current_status": "Waiting for Agent",
        "total_crashes_handled": 42,
        "last_crash_time": "2026-05-03 18:00:00",
        "last_error_summary": "KeyError: 'token'",
    }
    status_file.write_text(json.dumps(test_status, indent=2))

    response = client.get("/api/watchdog/status")
    assert response.status_code == 200
    data = response.json()
    assert data["current_status"] == "Waiting for Agent"
    assert data["total_crashes_handled"] == 42
    assert data["last_crash_time"] == "2026-05-03 18:00:00"
    assert data["last_error_summary"] == "KeyError: 'token'"
    print("[PASS] Existing watchdog_status.json -> contents returned correctly")

    # Cleanup: restore original file if it existed
    if backup is not None:
        status_file.write_text(backup)
    elif status_file.exists():
        status_file.unlink()

    print("\nAll tests passed!")


if __name__ == "__main__":
    run()
