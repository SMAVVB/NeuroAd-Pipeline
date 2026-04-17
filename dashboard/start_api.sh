#!/bin/bash
# FastAPI Backend Start Script for NeuroAd Pipeline
# This script starts the FastAPI backend server on port 8080

set -e

# Configuration
PROJECT_DIR="$HOME/neuro_pipeline_project"
API_DIR="$PROJECT_DIR/dashboard/api"
LOG_DIR="$API_DIR/logs"
PID_FILE="$API_DIR/fastapi.pid"
ENV_PYTHON="$PROJECT_DIR/venv_rocm/bin/python"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Activate virtual environment
source "$PROJECT_DIR/venv_rocm/bin/activate"

# Change to project directory
cd "$PROJECT_DIR"

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "FastAPI server is already running with PID $PID"
        exit 0
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

echo "Starting FastAPI backend server on port 8080..."
echo "Log file: $LOG_DIR/fastapi.log"

# Start uvicorn in background
nohup uvicorn dashboard.api.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    > "$LOG_DIR/fastapi.log" 2>&1 &

# Save PID
echo $! > "$PID_FILE"

echo "FastAPI server started successfully with PID $(cat $PID_FILE)"
echo "Use 'tail -f $LOG_DIR/fastapi.log' to view logs"
echo "Endpoints:"
echo "  - GET  /api/campaigns"
echo "  - GET  /api/campaigns/{name}/scores"
echo "  - GET  /api/campaigns/{name}/brand"
echo "  - GET  /api/campaigns/{name}/brand-profile"
echo "  - GET  /api/campaigns/{name}/mirofish"
echo "  - GET  /health"
