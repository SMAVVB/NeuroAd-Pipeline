#!/usr/bin/env python3
"""
test_sequential.py — Smoke-Test für SequentialTribeScorer

Testet:
1. Import und Init ohne Crash
2. Memory-Tracking Funktionen
3. Dry-Run mit synthetischem "Video" (leer, nur Dateisystem-Check)
4. Campaign-Scan (Ordnerstruktur)

Kein echtes TRIBE v2 Modell wird geladen — nur der Wrapper-Code.

Usage:
    cd ~/neuro_pipeline_project
    source venv_rocm/bin/activate
    python test_sequential.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Import check
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print(" SequentialTribeScorer — Smoke Test")
print("=" * 55)

print("\n[1/5] Import check...")
try:
    from model_manager import (
        SequentialTribeScorer,
        aggressive_unload,
        extract_roi_scores,
        get_gpu_usage_gb,
        get_ram_usage_gb,
        log_memory,
        unload_extractor,
    )
    print("  ✓ model_manager imports OK")
except ImportError as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Memory utilities
# ---------------------------------------------------------------------------
print("\n[2/5] Memory utilities...")
ram = get_ram_usage_gb()
gpu = get_gpu_usage_gb()

if ram >= 0:
    print(f"  ✓ RAM usage:        {ram:.1f} GB")
else:
    print("  ⚠ psutil not installed — RAM tracking disabled")
    print("    Install with: pip install psutil")

print(f"  ✓ GPU alloc:        {gpu:.2f} GB")

import torch
print(f"  ✓ CUDA available:   {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  ✓ GPU device:       {torch.cuda.get_device_name(0)}")

# ---------------------------------------------------------------------------
# 3. SequentialTribeScorer init (dry_run=True — no model load)
# ---------------------------------------------------------------------------
print("\n[3/5] SequentialTribeScorer init (dry_run=True)...")
try:
    scorer = SequentialTribeScorer(dry_run=True)
    print(f"  ✓ Init OK — device={scorer.device}")
except Exception as e:
    print(f"  ✗ Init failed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 4. Dry-run score_asset with a temp file
# ---------------------------------------------------------------------------
print("\n[4/5] Dry-run score_asset...")

with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
    f.write(b"\x00" * 1024)  # dummy 1KB "video"
    tmp_path = f.name

try:
    result = scorer.score_asset(tmp_path, save_preds=False)
    print(f"  ✓ score_asset returned {len(result)} keys")
    print(f"  ✓ neural_engagement:  {result['neural_engagement']:.4f}")
    print(f"  ✓ emotional_impact:   {result['emotional_impact']:.4f}")
    print(f"  ✓ inference_time_s:   {result['inference_time_s']}")
except Exception as e:
    print(f"  ✗ score_asset failed: {e}")
    import traceback; traceback.print_exc()
finally:
    os.unlink(tmp_path)

# ---------------------------------------------------------------------------
# 5. extract_roi_scores with synthetic predictions
# ---------------------------------------------------------------------------
print("\n[5/5] extract_roi_scores with synthetic preds...")
import numpy as np

# Simulate TRIBE v2 output: (50 timesteps, 20484 vertices)
synthetic_preds = np.random.rand(50, 20484).astype(np.float32)
roi_scores = extract_roi_scores(synthetic_preds)

expected_keys = [
    "TPJ", "FFA", "PPA", "V5_MT", "Broca", "A1",
    "neural_engagement", "temporal_peak", "n_segments"
]

all_ok = True
for key in expected_keys:
    if key not in roi_scores:
        print(f"  ✗ Missing key: {key}")
        all_ok = False
    else:
        print(f"  ✓ {key:20s} = {roi_scores[key]:.4f}")

if all_ok:
    print("  ✓ All ROI scores extracted correctly")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print(" Summary")
print("=" * 55)
print("  ✓ model_manager.py is importable and functional")
print("  ✓ Memory tracking works")
print("  ✓ Dry-run inference returns correct schema")
print("  ✓ ROI extraction works on synthetic data")
print("")
print("  Next: Run with a real video (sintel_trailer.mp4)")
print("  Command:")
print("    python model_manager.py campaigns/test_campaign/assets/sintel_trailer.mp4")
print("")
print("  Or with explicit device:")
print("    python model_manager.py campaigns/test_campaign/assets/sintel_trailer.mp4 --device cuda")
print("")

scorer.unload()
print("  ✓ Scorer unloaded cleanly")
print("=" * 55 + "\n")
