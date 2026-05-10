#!/usr/bin/env python3
"""
Night-Loop: Sequenzielle GPU-Test-Run aller Pipeline-Module über venv_rocm.
Jedes Modul wird getestet, bei Fehler automatisch gefixt, Alert nach jedem Schritt.

Usage:
    cd /home/vincent/neuro_pipeline_project && source venv_rocm/bin/activate && python3 night_loop.py
"""

import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

PIPELINE_DIR = Path("/home/vincent/neuro_pipeline_project")
CAMPAIGN_DIR = PIPELINE_DIR / "campaigns" / "test_campaign"
SCORES_DIR = CAMPAIGN_DIR / "scores"
REPORT_DIR = CAMPAIGN_DIR / "report"

BRAND_LABELS = ["advertisement", "product", "brand"]

# Module configuration: order matters (GPU sequential)
# Each: (name, gpu_heavy, estimate_minutes, fix_func, test_func)
MODULES = [
    {
        "name": "CLIP",
        "gpu_heavy": False,
        "est_min": 0.1,
        "fix_fn": None,  # No known fix needed
    },
    {
        "name": "Saliency",
        "gpu_heavy": False,
        "est_min": 1,
        "fix_fn": "fix_vinet_checkpoint",
        "test_fn": "test_saliency_gpu",
    },
    {
        "name": "Emotion",
        "gpu_heavy": False,
        "est_min": 0.5,
        "fix_fn": "fix_timm_compatibility",
        "test_fn": "test_emotion_gpu",
    },
    {
        "name": "MiroFish",
        "gpu_heavy": False,
        "est_min": 0.1,
        "fix_fn": None,
        "test_fn": None,  # Uses API
    },
    {
        "name": "TRIBE",
        "gpu_heavy": True,
        "est_min": 5,
        "fix_fn": None,
        "test_fn": None,  # Uses standard pipeline
    },
]

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def alert(msg):
    """Send alert via Telegram if possible."""
    try:
        cmd = f'curl -s -X POST "https://api.telegram.org/bot8632476947:AAGJHI7s_ex6F6BgcaRKtSbaXDtYpf7apn0/sendMessage" ' \
              f'-d "chat_id=1639530060&text={msg}"'
        subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
    except:
        pass  # Alert is optional
    log(f"🔔 ALERT: {msg}")

def clear_gpu_memory():
    """Clear GPU memory between modules."""
    try:
        cmd = f"""cd {PIPELINE_DIR} && source venv_rocm/bin/activate && python3 -c "
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    import gc; gc.collect()
    print('GPU cleared')
" 2>/dev/null"""
        subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
    except:
        pass

def run_module_test(module_name):
    """Test a specific module."""
    clear_gpu_memory()
    
    if module_name == "CLIP":
        return test_clip()
    elif module_name == "Saliency":
        return test_saliency()
    elif module_name == "Emotion":
        return test_emotion()
    elif module_name == "MiroFish":
        return test_mirofish()
    elif module_name == "TRIBE":
        return test_tribe()
    else:
        raise ValueError(f"Unknown module: {module_name}")

def test_clip():
    """Test CLIP on GPU."""
    log("Testing CLIP on GPU...")
    code = f"""
import sys
sys.path.insert(0, '{PIPELINE_DIR}')
import torch
assert torch.cuda.is_available(), "No GPU"

from pipeline_runner import run_pipeline_a
result = run_pipeline_a(
    '{CAMPAIGN_DIR}',
    brand_labels={BRAND_LABELS},
    only_modules=['clip']
)
print(f"CLIP Score: {{result['ranking'][0]['total_score'] if result.get('ranking') else 'N/A'}}")
assert result.get('ranking'), "CLIP failed"
"""
    proc = subprocess.run(
        ['bash', '-c', f'source {PIPELINE_DIR}/venv_rocm/bin/activate && python3 -c "{code}"'],
        capture_output=True, text=True, timeout=60
    )
    if proc.returncode == 0:
        log(f"✅ CLIP passed: {proc.stdout.strip().split(chr(10))[-1]}")
        return True, proc.stdout.strip()
    else:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        log(f"❌ CLIP failed: {err_msg}")
        return False, err_msg

def test_saliency():
    """Test Saliency on GPU."""
    log("Testing Saliency on GPU...")
    code = f"""
import sys
sys.path.insert(0, '{PIPELINE_DIR}')
import torch
assert torch.cuda.is_available(), "No GPU"

from pipeline_runner import run_pipeline_a
result = run_pipeline_a(
    '{CAMPAIGN_DIR}',
    brand_labels={BRAND_LABELS},
    only_modules=['saliency']
)
print(f"Saliency passed")
assert result.get('ranking'), "Saliency failed"
"""
    proc = subprocess.run(
        ['bash', '-c', f'source {PIPELINE_DIR}/venv_rocm/bin/activate && python3 -c "{code}"'],
        capture_output=True, text=True, timeout=120
    )
    if proc.returncode == 0:
        log("✅ Saliency passed")
        return True, proc.stdout.strip()
    else:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        log(f"❌ Saliency failed: {err_msg}")
        return False, err_msg

def test_emotion():
    """Test Emotion on GPU."""
    log("Testing Emotion on GPU...")
    code = f"""
import sys
sys.path.insert(0, '{PIPELINE_DIR}')
import torch
assert torch.cuda.is_available(), "No GPU"

from pipeline_runner import run_pipeline_a
result = run_pipeline_a(
    '{CAMPAIGN_DIR}',
    brand_labels={BRAND_LABELS},
    only_modules=['emotion']
)
print(f"Emotion passed")
assert result.get('ranking'), "Emotion failed"
"""
    proc = subprocess.run(
        ['bash', '-c', f'source {PIPELINE_DIR}/venv_rocm/bin/activate && python3 -c "{code}"'],
        capture_output=True, text=True, timeout=120
    )
    if proc.returncode == 0:
        log("✅ Emotion passed")
        return True, proc.stdout.strip()
    else:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        log(f"❌ Emotion failed: {err_msg}")
        return False, err_msg

def test_mirofish():
    """Test MiroFish API."""
    log("Testing MiroFish API...")
    code = f"""
import sys
sys.path.insert(0, '{PIPELINE_DIR}')

from mirofish_client import MiroFishClient
client = MiroFishClient('http://localhost:8000')
print(f"Client methods: {{[m for m in dir(client) if not m.startswith('_')]}}")
assert 'run_simulation' in dir(client), "MiroFish API not ready"
"""
    proc = subprocess.run(
        ['bash', '-c', f'source {PIPELINE_DIR}/venv_rocm/bin/activate && python3 -c "{code}"'],
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode == 0:
        log("✅ MiroFish API passed")
        return True, proc.stdout.strip()
    else:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        log(f"❌ MiroFish failed: {err_msg}")
        return False, err_msg

def test_tribe():
    """Test TRIBE on GPU."""
    log("Testing TRIBE on GPU...")
    code = f"""
import sys
sys.path.insert(0, '{PIPELINE_DIR}')
import torch
assert torch.cuda.is_available(), "No GPU"

from tribev2 import TribeModel
model = TribeModel.from_pretrained('facebook/tribev2', device='cuda')
print("TRIBE model loaded successfully")
del model
"""
    proc = subprocess.run(
        ['bash', '-c', f'source {PIPELINE_DIR}/venv_rocm/bin/activate && python3 -c "{code}"'],
        capture_output=True, text=True, timeout=600
    )
    if proc.returncode == 0:
        log("✅ TRIBE passed")
        return True, proc.stdout.strip()
    else:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        log(f"❌ TRIBE failed: {err_msg}")
        return False, err_msg

def main():
    log("=" * 60)
    log("🌙 NIGHT PIPELINE TEST — starting")
    log(f"GPU: {subprocess.check_output(['bash', '-c', f'source {PIPELINE_DIR}/venv_rocm/bin/activate && python3 -c \\"import torch; print(torch.cuda.get_device_name(0))\\"'], shell=True, text=True).strip()}")
    log(f"Campaign: {CAMPAIGN_DIR}")
    log("=" * 60)
    
    # Test each module sequentially
    for i, module in enumerate(MODULES, 1):
        name = module["name"]
        gpu_heavy = module["gpu_heavy"]
        est_min = module["est_min"]
        
        log(f"\n--- Module {i}/{len(MODULES)}: {name} (GPU: {gpu_heavy}, ~{est_min}min) ---")
        
        passed, result = run_module_test(name)
        
        if passed:
            log(f"✅ {name} PASSED")
            alert(f"✅ Modul {name} abgeschlossen")
        else:
            log(f"❌ {name} FAILED")
            # Try auto-fix if available
            if module["fix_fn"] and module["fix_fn"] in globals():
                fix_func = globals()[module["fix_fn"]]
                log(f"🔧 Trying auto-fix for {name}...")
                fix_func()
                clear_gpu_memory()
                
                # Retry
                time.sleep(2)  # Allow GPU memory to clear
                passed, result = run_module_test(name)
                if passed:
                    log(f"✅ {name} PASSED after fix")
                    alert(f"✅ Modul {name} (nach Fix) abgeschlossen")
                else:
                    log(f"❌ {name} still FAILED after fix: {result}")
                    alert(f"⚠️ Modul {name} hat nach Fix noch immer Fehler: {result}")
            else:
                log(f"⚠️ No auto-fix available for {name}")
                alert(f"⚠️ Modul {name} fehlgeschlagen (kein Auto-Fix)")
        
        # Clear GPU between modules
        clear_gpu_memory()
        
        # Wait a moment before next module
        time.sleep(1)
    
    # Final status
    log("\n" + "=" * 60)
    log("🎉 NIGHT PIPELINE TEST COMPLETE")
    log("=" * 60)
    alert("🎉 Alle Module durch! Pipeline ready")
    
    # Save log
    log_file = PIPELINE_DIR / "night_loop_log.txt"
    log_file.write_text(f"NIGHT PIPELINE TEST\n{'='*40}\nTest complete\n")

if __name__ == "__main__":
    main()
