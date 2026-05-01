#!/bin/bash

cd ~/neuro_pipeline_project
source venv_rocm/bin/activate
LOG=~/neuro_pipeline_project/run_apple_tonight.log

echo "========================================" >> $LOG
echo "START: $(date)" >> $LOG
echo "========================================" >> $LOG

# PHASE 1: Brand Research (~2-3h)
echo "PHASE 1: Brand Research START $(date)" >> $LOG
python3 brand_orchestrator.py "Apple" >> $LOG 2>&1
echo "PHASE 1: Brand Research DONE $(date)" >> $LOG

# PHASE 2: Pipeline A (~2-3h)
echo "PHASE 2: Pipeline START $(date)" >> $LOG
python3 pipeline_runner.py \
  --campaign-dir campaigns/apple \
  --brand-labels "apple" "iphone" "premium" "minimalist" "think different" \
  >> $LOG 2>&1
echo "PHASE 2: Pipeline DONE $(date)" >> $LOG

# PHASE 3: Report Agent (~30min)
echo "PHASE 3: Report START $(date)" >> $LOG
python3 report_agent/report_orchestrator.py \
  --campaign-dir campaigns/apple \
  >> $LOG 2>&1
echo "PHASE 3: Report DONE $(date)" >> $LOG

echo "========================================" >> $LOG
echo "ALL DONE: $(date)" >> $LOG
echo "========================================" >> $LOG
