#!/usr/bin/env bash
# =============================================================================
# apply_patches.sh — NeuroAd Pipeline neuralset patches
# =============================================================================
# Run this after any pip install that might overwrite neuralset.
# These patches enable GPU-compatible sequential inference on The Beast.
#
# Usage:
#   cd ~/neuro_pipeline_project
#   source venv_rocm/bin/activate
#   bash apply_patches.sh
#
# What this patches:
#   1. neuralset/extractors/video.py  — V-JEPA2 device handling
#   2. neuralset/extractors/audio.py  — Wav2Vec/Bert device handling
#   3. neuralset/extractors/text.py   — LLaMA device handling
#   4. tribev2/eventstransforms.py    — WhisperX int8 + cpu
# =============================================================================

set -euo pipefail

VENV_DIR="${VENV_DIR:-$(pwd)/venv_rocm}"
NEURALSET_DIR="$VENV_DIR/lib/python3.12/site-packages/neuralset"
TRIBE_DIR="$(pwd)/tools/tribev2/tribev2"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
log_warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
log_err()  { echo -e "${RED}  ✗ $1${NC}"; }
log_info() { echo -e "${CYAN}  → $1${NC}"; }

echo ""
echo "=============================================="
echo " NeuroAd neuralset patch script"
echo "=============================================="
echo " VENV:      $VENV_DIR"
echo " NEURALSET: $NEURALSET_DIR"
echo " TRIBE:     $TRIBE_DIR"
echo ""

# ---------------------------------------------------------------------------
# Helper: apply a Python sed-like replacement
# ---------------------------------------------------------------------------
apply_patch() {
    local file="$1"
    local description="$2"
    local old_pattern="$3"
    local new_pattern="$4"

    if [ ! -f "$file" ]; then
        log_err "File not found: $file"
        return 1
    fi

    # Check if patch is already applied (new_pattern already present)
    if grep -qF "$new_pattern" "$file"; then
        log_ok "Already patched: $description"
        return 0
    fi

    # Check if old pattern exists to replace
    if grep -qF "$old_pattern" "$file"; then
        # Create backup before first patch of this file
        if [ ! -f "${file}.orig" ]; then
            cp "$file" "${file}.orig"
            log_info "Backup created: ${file}.orig"
        fi
        # Use Python for reliable multiline-safe replacement
        python3 - "$file" "$old_pattern" "$new_pattern" <<'PYEOF'
import sys
path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
content = open(path).read()
if old not in content:
    print(f"Pattern not found in {path}", file=sys.stderr)
    sys.exit(1)
open(path, 'w').write(content.replace(old, new, 1))
PYEOF
        log_ok "Patched: $description"
    else
        log_warn "Pattern not found (skipping): $description"
        log_warn "  Expected: $old_pattern"
    fi
}

# ---------------------------------------------------------------------------
# Patch 1: video.py — _HFVideoModel device placement
# ---------------------------------------------------------------------------
echo "── video.py ──────────────────────────────────"
VIDEO_FILE="$NEURALSET_DIR/extractors/video.py"

apply_patch "$VIDEO_FILE" \
    "vjepa2 model to cuda-or-cpu" \
    'self.model = self.model.to("cuda" if torch.cuda.is_available() else "cpu")' \
    'self.model = self.model.to("cuda" if torch.cuda.is_available() else "cpu")  # patched: device already handled by SequentialTribeScorer'

# Patch resamp_first_dim — uses bare `self.device` which is undefined in module scope
apply_patch "$VIDEO_FILE" \
    "resamp_first_dim self.device bug" \
    '    ).to(self.device)' \
    '    ).to("cuda" if torch.cuda.is_available() else "cpu")'

# ---------------------------------------------------------------------------
# Patch 2: audio.py — Wav2VecBert + Whisper device
# ---------------------------------------------------------------------------
echo ""
echo "── audio.py ──────────────────────────────────"
AUDIO_FILE="$NEURALSET_DIR/extractors/audio.py"

# Wav2VecBert
apply_patch "$AUDIO_FILE" \
    "Wav2VecBert _get_sound_model device" \
    '        _model = Wav2Vec2BertModel.from_pretrained(model_name)
        _model.to(self.device)' \
    '        _model = Wav2Vec2BertModel.from_pretrained(model_name)
        _model.to("cuda" if torch.cuda.is_available() else "cpu")'

# Whisper encoder
apply_patch "$AUDIO_FILE" \
    "Whisper _get_sound_model device" \
    '        _model = WhisperModel.from_pretrained(
            model_name, torch_dtype=torch.float32
        ).encoder
        _model.to(self.device)' \
    '        _model = WhisperModel.from_pretrained(
            model_name, torch_dtype=torch.float32
        ).encoder
        _model.to("cuda" if torch.cuda.is_available() else "cpu")'

# HuggingFaceAudio base _get_sound_model
apply_patch "$AUDIO_FILE" \
    "HuggingFaceAudio base _get_sound_model device" \
    '        _model = AutoModel.from_pretrained(model_name)
        _model.to(self.device)' \
    '        _model = AutoModel.from_pretrained(model_name)
        _model.to("cuda" if torch.cuda.is_available() else "cpu")'

# ---------------------------------------------------------------------------
# Patch 3: text.py — HuggingFaceText device
# ---------------------------------------------------------------------------
echo ""
echo "── text.py ───────────────────────────────────"
TEXT_FILE="$NEURALSET_DIR/extractors/text.py"

apply_patch "$TEXT_FILE" \
    "HuggingFaceText _load_model device placement" \
    '        if self.device != "accelerate":
            model.to(self.device)' \
    '        if self.device != "accelerate":
            model.to("cuda" if torch.cuda.is_available() else "cpu")'

# ---------------------------------------------------------------------------
# Patch 4: eventstransforms.py — WhisperX int8 + cpu
# ---------------------------------------------------------------------------
echo ""
echo "── eventstransforms.py ───────────────────────"
EVENTS_FILE="$TRIBE_DIR/eventstransforms.py"

if [ ! -f "$EVENTS_FILE" ]; then
    # Try alternate path
    EVENTS_FILE="$(pwd)/tools/tribev2/tribev2/eventstransforms.py"
fi

if [ -f "$EVENTS_FILE" ]; then
    # compute_type float16 → int8
    apply_patch "$EVENTS_FILE" \
        "WhisperX compute_type float16->int8" \
        'compute_type="float16"' \
        'compute_type="int8"'

    # WhisperX device cpu (avoids ROCm issues with WhisperX)
    apply_patch "$EVENTS_FILE" \
        "WhisperX device cuda->cpu" \
        'device="cuda"' \
        'device="cpu"'
else
    log_warn "eventstransforms.py not found at $EVENTS_FILE — skipping WhisperX patch"
fi

# ---------------------------------------------------------------------------
# Patch 5: demo_utils.py — device segfault fix (line ~193)
# ---------------------------------------------------------------------------
echo ""
echo "── demo_utils.py ─────────────────────────────"
DEMO_FILE="$(pwd)/tools/tribev2/tribev2/demo_utils.py"

if [ ! -f "$DEMO_FILE" ]; then
    DEMO_FILE="$TRIBE_DIR/../demo_utils.py"
fi

if [ -f "$DEMO_FILE" ]; then
    # The segfault fix: device = "cuda" → device = "cpu" at checkpoint load
    # Only patch the checkpoint-loading context, not the full inference device
    apply_patch "$DEMO_FILE" \
        "demo_utils checkpoint load device cpu (segfault fix)" \
        '            device = "cuda" if torch.cuda.is_available() else "cpu"' \
        '            device = "cpu"  # patched: prevents ROCm segfault during checkpoint load'
else
    log_warn "demo_utils.py not found — skipping checkpoint device patch"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "=============================================="
echo " Patch summary"
echo "=============================================="

PATCH_COUNT=0
for f in "$VIDEO_FILE" "$AUDIO_FILE" "$TEXT_FILE" "$EVENTS_FILE"; do
    if [ -f "${f}.orig" ]; then
        PATCH_COUNT=$((PATCH_COUNT + 1))
        log_info "Backup exists: ${f##*/}.orig"
    fi
done

echo ""
log_ok "Patches applied. TRIBE v2 is ready for sequential inference."
echo ""
echo "  Next step:"
echo "    python model_manager.py campaigns/test_campaign/assets/sintel_trailer.mp4"
echo ""
