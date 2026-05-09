#!/bin/bash
CAMPAIGN=${1:-"campaigns/nike_summer_26"}
LOG_FILE="/home/vincent/neuro_pipeline_project/hermes_run_$(date +%Y%m%d_%H%M%S).log"
VENV="/home/vincent/neuro_pipeline_project/venv_rocm/bin/python"

echo "=== HERMES PIPELINE RUN ===" > "$LOG_FILE"
echo "Start: $(date)" >> "$LOG_FILE"
echo "Campaign: $CAMPAIGN" >> "$LOG_FILE"
echo "===========================" >> "$LOG_FILE"

$VENV pipeline_runner.py "$CAMPAIGN" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "===========================" >> "$LOG_FILE"
echo "End: $(date)" >> "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" >> "$LOG_FILE"
grep -E "ERROR|WARNING|Score|Grade|✓|✗|FAIL|SUCCESS|Traceback" "$LOG_FILE" | tail -50

echo "LOG: $LOG_FILE"
echo "EXIT: $EXIT_CODE"
