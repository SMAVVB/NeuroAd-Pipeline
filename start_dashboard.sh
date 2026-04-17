#!/bin/bash

# Startet FastAPI Backend + Next.js Dashboard

cd ~/neuro_pipeline_project

source venv_rocm/bin/activate


# FastAPI Backend
nohup uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8080 > dashboard/api/server.log 2>&1 &

echo "FastAPI Backend gestartet auf Port 8080"


# Next.js Dashboard
cd dashboard_v2

nohup npm run dev > ../dashboard_dev.log 2>&1 &

echo "Dashboard gestartet auf Port 3000"


echo "Logs: dashboard/api/server.log und dashboard_dev.log"
