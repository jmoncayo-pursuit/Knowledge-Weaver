#!/bin/bash

# Kill existing processes on ports 8000 and 8080
echo "Stopping existing servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Ensure logs directory exists
mkdir -p logs

# Start Backend
echo "Starting Backend..."
cd backend_api
# Check if venv exists, if so activate it
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi
nohup uvicorn main:app --reload --port 8000 > ../logs/server.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID. Logs: logs/server.log"

# Start Frontend
echo "Starting Frontend..."
cd ../app_dashboard
nohup python3 -m http.server 8080 > ../logs/dashboard.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID $FRONTEND_PID. Logs: logs/dashboard.log"

cd ..
echo "Servers are running."
