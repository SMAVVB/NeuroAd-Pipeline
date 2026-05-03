"""
Watchdog: monitors campaign logs for errors and creates Multica tickets.
Includes an infinite-loop guard that tracks crash locations to avoid
false positives when the same generic error occurs in different files.
"""

import hashlib
import json
import os
import re
import sys

GUARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".watchdog_loop_guard.json")
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchdog_status.json")

# Current watchdog lifecycle state
_watchdog_status = {
    "last_crash_time": None,
    "total_crashes_handled": 0,
    "current_status": "Monitoring",
    "last_error_summary": None,
}


def extract_location(raw_trace: str) -> str:
    """Extract the last file path and line number from a raw traceback string.

    Looks for patterns like '  File "path/to/file.py", line 123' and returns
    the last occurrence's file:line combo.

    Args:
        raw_trace: The full traceback / error string.

    Returns:
        A string like 'path/to/file.py:123', or 'unknown:0' if nothing found.
    """
    pattern = r'File "([^"]+)", line (\d+)'
    matches = re.findall(pattern, raw_trace)
    if matches:
        _, last_line = matches[-1]
        return f"{matches[-1][0]}:{last_line}"
    return "unknown:0"


def compute_error_hash(error_summary: str, raw_trace: str) -> str:
    """Generate an MD5 hash based on error_summary AND the crash location.

    Combining the error summary with the file:line location ensures that
    identical errors in different files produce different hashes, preventing
    false "infinite loop" detections.

    Args:
        error_summary: The summarized error message (e.g. "TypeError: unhashable type: 'dict'").
        raw_trace: The full traceback / error string.

    Returns:
        Hex digest of the MD5 hash.
    """
    location = extract_location(raw_trace)
    hash_input = f"{error_summary}|{location}"
    return hashlib.md5(hash_input.encode("utf-8")).hexdigest()


def load_guard_state() -> dict:
    """Load the loop guard state from disk, or return an empty dict."""
    if os.path.exists(GUARD_FILE):
        try:
            with open(GUARD_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_guard_state(state: dict):
    """Save the loop guard state to disk."""
    with open(GUARD_FILE, "w") as f:
        json.dump(state, f, indent=2)


def set_status(status: str):
    """Set the current watchdog lifecycle status.

    Args:
        status: One of 'Monitoring', 'Cooling Down',
            'Waiting for Agent', 'Fatal Error'.
    """
    _watchdog_status["current_status"] = status
    _write_status()


def record_crash(error_summary: str):
    """Record a crash event and update the watchdog status.

    Args:
        error_summary: The summarized error message from the crash.
    """
    from datetime import datetime

    _watchdog_status["total_crashes_handled"] += 1
    _watchdog_status["last_crash_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _watchdog_status["last_error_summary"] = error_summary
    _watchdog_status["current_status"] = "Waiting for Agent"
    _write_status()


def _write_status():
    """Write the current watchdog status to disk synchronously."""
    with open(STATUS_FILE, "w") as f:
        json.dump(_watchdog_status, f, indent=2)


def get_watchdog_status() -> dict:
    """Return the current watchdog status dict (copy).

    Returns:
        A copy of the internal status dictionary.
    """
    return dict(_watchdog_status)


def load_watchdog_status() -> dict:
    """Load the watchdog status from disk.

    Returns:
        The status dict from the JSON file, or the in-memory default
        if the file does not exist.
    """
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return dict(_watchdog_status)


def create_multica_ticket(error_summary: str, raw_trace: str) -> dict:
    """Create a Multica ticket for the given error, with infinite-loop detection.

    Checks the loop guard state to determine if this exact error at this
    exact location has occurred too frequently. If so, raises a fatal error
    instead of creating a new ticket.

    Args:
        error_summary: Summarized error message.
        raw_trace: Full traceback string.

    Returns:
        dict with 'action' ('created' or 'duplicate') and 'hash' keys.

    Raises:
        RuntimeError: If the infinite-loop threshold is exceeded.
    """
    hash_value = compute_error_hash(error_summary, raw_trace)
    guard = load_guard_state()

    # Track per-hash: count and last seen timestamp
    if hash_value in guard:
        guard[hash_value]["count"] += 1
        guard[hash_value]["last_seen"] = _now_iso()
    else:
        guard[hash_value] = {
            "count": 1,
            "first_seen": _now_iso(),
            "last_seen": _now_iso(),
            "error_summary": error_summary,
        }

    save_guard_state(guard)

    # Threshold: after 5 occurrences of the same error at the same location,
    # treat it as an infinite loop.
    infinite_loop_threshold = 5
    if guard[hash_value]["count"] >= infinite_loop_threshold:
        set_status("Fatal Error")
        raise RuntimeError(
            f"Infinite Loop Detected: '{error_summary}' at {extract_location(raw_trace)} "
            f"has occurred {guard[hash_value]['count']} times. "
            f"Manual intervention required."
        )

    if guard[hash_value]["count"] > 1:
        set_status("Monitoring")
        return {"action": "duplicate", "hash": hash_value}

    # For first occurrence, create a new ticket (placeholder).
    record_crash(error_summary)
    return {"action": "created", "hash": hash_value}


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    # Quick smoke test.
    sample_trace = """
  File "/home/vincent/neuro_pipeline_project/master_orchestrator.py", line 142
    result = process(data)
  File "/home/vincent/neuro_pipeline_project/agents/agent_social.py", line 89
    return dict[key]
TypeError: unhashable type: 'dict'
"""
    error = "TypeError: unhashable type: 'dict'"
    result = create_multica_ticket(error, sample_trace)
    print(json.dumps(result, indent=2))
    print("Hash:", result["hash"])
