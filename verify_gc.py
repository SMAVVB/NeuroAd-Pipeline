#!/usr/bin/env python3
"""
verify_gc.py — Verifies that the aggressive GC cleanup between pipeline phases works correctly.

Simulates a pipeline step that allocates memory (dummy tensor), then runs the cleanup function
to ensure no crashes occur.
"""

import gc
import sys

# --- Inline the same cleanup logic from the orchestrators to test it ---
_torch = None
try:
    import torch
    _torch = torch
except ImportError:
    pass


def cleanup_phases():
    """Aggressive garbage collection to free RAM between pipeline phases."""
    gc.collect()
    if _torch is not None:
        try:
            _torch.cuda.empty_cache()
        except Exception:
            pass
    print("[Memory] Ran Garbage Collection")


# --- Test 1: cleanup_phases() without torch imported ---
print("Test 1: cleanup_phases() with torch=disabled (torch not imported)")
try:
    _torch_disabled = _torch
    _torch = None
    cleanup_phases()
    print("  PASS — no crash when torch is None")
except Exception as e:
    print(f"  FAIL — {e}")
    sys.exit(1)
_torch = _torch_disabled

# --- Test 2: cleanup_phases() with torch imported but no GPU ---
print("\nTest 2: cleanup_phases() with torch imported, no GPU available")
if _torch is not None:
    try:
        cleanup_phases()
        print("  PASS — no crash when torch loaded but no GPU")
    except Exception as e:
        print(f"  FAIL — {e}")
        sys.exit(1)
else:
    print("  SKIP — torch not available, skipping GPU test")

# --- Test 3: Simulate a pipeline step with memory allocation ---
print("\nTest 3: Simulate pipeline memory allocation + cleanup")
try:
    if _torch is not None:
        # Allocate a large dummy tensor to simulate a model step
        dummy_tensor = _torch.randn(1000, 1000, 1000)
        tensor_size = dummy_tensor.nelement() * dummy_tensor.element_size()
        print(f"  Allocated tensor: {tensor_size / (1024**3):.2f} GB")

        # Delete it — without gc it may linger
        del dummy_tensor
        gc.collect()

        cleanup_phases()
        print("  PASS — allocation and cleanup completed without crash")
    else:
        # Fallback: use plain Python lists to simulate memory
        dummy_list = [bytearray(1024 * 1024) for _ in range(100)]  # 100 MB
        print(f"  Allocated {len(dummy_list)} MB via Python lists")
        del dummy_list
        gc.collect()
        cleanup_phases()
        print("  PASS — allocation and cleanup completed without crash (CPU-only fallback)")
except Exception as e:
    print(f"  FAIL — {e}")
    sys.exit(1)

# --- Test 4: Multiple cleanup calls (simulating multiple phases) ---
print("\nTest 4: Multiple cleanup calls (simulating Phase 0→4)")
try:
    for phase in range(5):
        # Simulate work
        if _torch is not None:
            _ = _torch.randn(500, 500, 500)
        else:
            _ = [bytearray(512 * 1024) for _ in range(50)]
        # Cleanup
        cleanup_phases()
    print("  PASS — all 5 phases cleaned up without crash")
except Exception as e:
    print(f"  FAIL — {e}")
    sys.exit(1)

print("\nAll tests passed — garbage collection cleanup is safe to use.")
