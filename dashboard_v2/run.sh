#!/bin/bash
cd ~/neuro_pipeline_project/dashboard_v2

# Install Python dependencies
pip install fastapi uvicorn httpx python-multipart --quiet

# Install Node dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start FastAPI backend
echo "Starting API server on port 8000..."
cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
cd ..

# Wait for API
sleep 2

# Start Vite dev server
echo "Starting frontend on port 3001..."
cd ~/neuro_pipeline_project/dashboard_v2/frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✓ NeuroAd Dashboard running:"
echo "  Local:   http://localhost:3001"
echo "  Network: http://$(hostname -I | awk '{print $1}'):3001"
echo ""
echo "Press Ctrl+C to stop"

# Cleanup on exit
trap "kill $API_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
