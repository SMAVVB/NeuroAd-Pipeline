"""Verification script for watchdog_status.json integration.

Imports helper functions from watchdog.py, exercises the status update
path, then reads the JSON file on disk to assert correctness.
"""

import json
import os
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def run():
    # Point watchdog files to a temp directory so we don't pollute real state.
    import watchdog

    with tempfile.TemporaryDirectory() as td:
        watchdog.GUARD_FILE = os.path.join(td, ".watchdog_loop_guard.json")
        watchdog.STATUS_FILE = os.path.join(td, "watchdog_status.json")

        # Reset in-memory state
        watchdog._watchdog_status = {
            "last_crash_time": None,
            "total_crashes_handled": 0,
            "current_status": "Monitoring",
            "last_error_summary": None,
        }

        # --- Test 1: Initial status ---
        status = watchdog.get_watchdog_status()
        assert status["current_status"] == "Monitoring", (
            f"Expected 'Monitoring', got {status['current_status']}"
        )
        assert status["total_crashes_handled"] == 0
        print("[PASS] Initial status is Monitoring with 0 crashes")

        # --- Test 2: record_crash updates in-memory and on-disk ---
        watchdog.record_crash("ValueError: bad input")
        status = watchdog.get_watchdog_status()
        assert status["current_status"] == "Waiting for Agent"
        assert status["total_crashes_handled"] == 1
        assert status["last_error_summary"] == "ValueError: bad input"
        assert status["last_crash_time"] is not None
        print(f"[PASS] record_crash: status={status['current_status']}, "
              f"crashes={status['total_crashes_handled']}")

        # Verify on-disk JSON matches
        with open(watchdog.STATUS_FILE, "r") as f:
            disk_status = json.load(f)
        assert disk_status["total_crashes_handled"] == 1
        assert disk_status["current_status"] == "Waiting for Agent"
        assert disk_status["last_error_summary"] == "ValueError: bad input"
        print("[PASS] On-disk watchdog_status.json matches in-memory state")

        # --- Test 3: load_watchdog_status reads from disk ---
        loaded = watchdog.load_watchdog_status()
        assert loaded["last_error_summary"] == "ValueError: bad input"
        print("[PASS] load_watchdog_status returns correct on-disk values")

        # --- Test 4: set_status updates ---
        watchdog.set_status("Cooling Down")
        status = watchdog.get_watchdog_status()
        assert status["current_status"] == "Cooling Down"
        print("[PASS] set_status('Cooling Down') works")

        # --- Test 5: create_multica_ticket records a crash on first occurrence ---
        watchdog._watchdog_status = {
            "last_crash_time": None,
            "total_crashes_handled": 0,
            "current_status": "Monitoring",
            "last_error_summary": None,
        }
        result = watchdog.create_multica_ticket(
            "TypeError: unhashable type: 'dict'",
            '  File "/fake/path.py", line 42\nTypeError: unhashable type: \'dict\'',
        )
        assert result["action"] == "created"
        status = watchdog.get_watchdog_status()
        assert status["total_crashes_handled"] == 1
        assert status["current_status"] == "Waiting for Agent"
        assert status["last_error_summary"] == "TypeError: unhashable type: 'dict'"
        print("[PASS] create_multica_ticket records crash correctly")

        # --- Test 6: duplicate does not increment crash count ---
        watchdog._watchdog_status = {
            "last_crash_time": None,
            "total_crashes_handled": 0,
            "current_status": "Monitoring",
            "last_error_summary": None,
        }
        # First occurrence
        watchdog.create_multica_ticket(
            "TypeError: unhashable type: 'dict'",
            '  File "/fake/path.py", line 42\nTypeError: unhashable type: \'dict\'',
        )
        status = watchdog.get_watchdog_status()
        crash_count_first = status["total_crashes_handled"]

        # Reset guard so we can simulate duplicate
        watchdog._watchdog_status = {
            "last_crash_time": None,
            "total_crashes_handled": 0,
            "current_status": "Monitoring",
            "last_error_summary": None,
        }
        watchdog.save_guard_state({})
        # First call to seed guard
        watchdog.create_multica_ticket(
            "TypeError: unhashable type: 'dict'",
            '  File "/fake/path.py", line 42\nTypeError: unhashable type: \'dict\'',
        )
        # Reset again and call again to get duplicate
        watchdog._watchdog_status = {
            "last_crash_time": None,
            "total_crashes_handled": 0,
            "current_status": "Monitoring",
            "last_error_summary": None,
        }
        result = watchdog.create_multica_ticket(
            "TypeError: unhashable type: 'dict'",
            '  File "/fake/path.py", line 42\nTypeError: unhashable type: \'dict\'',
        )
        assert result["action"] == "duplicate"
        status = watchdog.get_watchdog_status()
        assert status["total_crashes_handled"] == crash_count_first, (
            "Duplicate should not increment crash count"
        )
        assert status["current_status"] == "Monitoring"
        print("[PASS] Duplicate events do not increment crash count")

        print("\nAll tests passed!")


if __name__ == "__main__":
    run()
