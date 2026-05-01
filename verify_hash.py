"""
verify_hash.py: Verifies that the watchdog loop guard hashing logic
correctly differentiates errors at different file/line locations.

Passes two identical error summaries with different stack traces
and asserts the hashes are DIFFERENT.

Exit code 0 = success, non-zero = failure.
"""

import sys
import os

# Ensure watchdog module is importable from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from watchdog import compute_error_hash

TRACE_A = """
  File "/home/vincent/neuro_pipeline_project/master_orchestrator.py", line 142
    result = process(data)
TypeError: unhashable type: 'dict'
"""

TRACE_B = """
  File "/home/vincent/neuro_pipeline_project/agents/agent_social.py", line 89
    return dict[key]
TypeError: unhashable type: 'dict'
"""

ERROR_SUMMARY = "TypeError: unhashable type: 'dict'"


def main():
    hash_a = compute_error_hash(ERROR_SUMMARY, TRACE_A)
    hash_b = compute_error_hash(ERROR_SUMMARY, TRACE_B)

    print(f"Error summary: {ERROR_SUMMARY}")
    print(f"Trace A hash:  {hash_a}")
    print(f"Trace B hash:  {hash_b}")

    # Core assertion: identical errors at different locations MUST produce different hashes.
    assert hash_a != hash_b, (
        f"FAIL: Hashes are identical ({hash_a}) for different stack traces. "
        "The loop guard will falsely merge distinct crash locations."
    )

    # Also verify the hash includes location info by checking extract_location.
    from watchdog import extract_location
    loc_a = extract_location(TRACE_A)
    loc_b = extract_location(TRACE_B)
    assert loc_a != loc_b, "FAIL: extract_location returned the same location for different traces."
    assert loc_a != "unknown:0", f"FAIL: extract_location failed to parse Trace A: {loc_a}"
    assert loc_b != "unknown:0", f"FAIL: extract_location failed to parse Trace B: {loc_b}"

    # Verify identical inputs produce identical hashes (deterministic).
    hash_a2 = compute_error_hash(ERROR_SUMMARY, TRACE_A)
    assert hash_a == hash_a2, "FAIL: Same inputs produced different hashes. Hash is non-deterministic."

    print("PASS: All assertions passed. Location-aware hashing works correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
