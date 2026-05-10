#!/bin/bash
BRAND=${1:-"nike"}
CAMPAIGN=${2:-"campaigns/nike_summer_26"}
VENV="/home/vincent/neuro_pipeline_project/venv_rocm/bin"
LOG_DIR="/home/vincent/neuro_pipeline_project"
TS=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/overnight_${BRAND}_${TS}.log"

notify() {
    python3 "$LOG_DIR/notify_discord.py" "$1" 2>/dev/null
}

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

cd /home/vincent/neuro_pipeline_project
source "$VENV/activate"

log "=== OVERNIGHT LOOP START: $BRAND ==="
notify "🌙 Overnight Loop gestartet: $BRAND"

# Phase 1: Brand Research (Pipeline B)
log "--- Phase 1: Brand Research ---"
notify "🔍 Phase 1: Brand Research läuft..."
python brand_orchestrator.py "$BRAND" >> "$LOG" 2>&1
RC=$?
if [ $RC -ne 0 ]; then
    notify "❌ Phase 1 FAILED (Exit $RC) — siehe $LOG"
    log "Phase 1 FAILED"
    exit 1
fi
notify "✅ Phase 1 abgeschlossen"
log "Phase 1 done"

# Phase 2: Pipeline A (Neural Scoring)
log "--- Phase 2: Pipeline A ---"
notify "🧠 Phase 2: Neural Scoring läuft..."
python pipeline_runner.py "$CAMPAIGN" >> "$LOG" 2>&1
RC=$?
SCORE=$(grep "COMPOSITE SCORE" "$LOG" | tail -1 | grep -oP '\d+\.\d+')
if [ $RC -ne 0 ]; then
    notify "❌ Phase 2 FAILED (Exit $RC) | Score: $SCORE — siehe $LOG"
    log "Phase 2 FAILED"
    exit 1
fi
notify "✅ Phase 2 abgeschlossen | Score: $SCORE"
log "Phase 2 done — Score: $SCORE"

# Phase 3: Report Agent
log "--- Phase 3: Report Agent ---"
notify "📊 Phase 3: Auswertung läuft..."
python report_agent/report_orchestrator.py --campaign "$CAMPAIGN" >> "$LOG" 2>&1
RC=$?
if [ $RC -ne 0 ]; then
    notify "❌ Phase 3 FAILED (Exit $RC) — siehe $LOG"
    log "Phase 3 FAILED"
    exit 1
fi
notify "✅ Phase 3 abgeschlossen"
log "Phase 3 done"

log "=== OVERNIGHT LOOP COMPLETE ==="
notify "🎉 Overnight Loop fertig: $BRAND | Score: $SCORE | Log: $LOG"
