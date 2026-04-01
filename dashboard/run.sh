#!/bin/bash
cd ~/neuro_pipeline_project
source venv_rocm/bin/activate
streamlit run dashboard/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.headless true \
  --theme.base dark
