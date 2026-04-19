#!/bin/bash

# Startet FastAPI Backend + Next.js Dashboard

set -e  # Exit on error

cd ~/neuro_pipeline_project

# Activate venv and log errors
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting FastAPI Backend..." >> start_dashboard.log
source venv_rocm/bin/activate 2>> start_dashboard.log || { echo "ERROR: Failed to activate venv" >> start_dashboard.log; exit 1; }

# FastAPI Backend
nohup uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8080 > dashboard/api/server.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Health check
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] FastAPI Backend started successfully (PID: $BACKEND_PID)" >> start_dashboard.log
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: FastAPI Backend failed to start. Check dashboard/api/server.log" >> start_dashboard.log
    cat dashboard/api/server.log
fi

echo "FastAPI Backend gestartet auf Port 8080"


# Next.js Dashboard
cd dashboard_v2

nohup npm run dev > ../dashboard_dev.log 2>&1 &
DASHBOARD_PID=$!

echo "Dashboard gestartet auf Port 3000"


echo "Logs: dashboard/api/server.log, start_dashboard.log und dashboard_dev.log"
