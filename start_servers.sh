#!/bin/bash
# Kill existing servers confidently
echo "Stopping existing servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null
pkill -f uvicorn
pkill -f http.server

# Wait for ports to clear
sleep 2

# Start Backend
cd /Users/jmoncayopursuit.org/Desktop/kiro-dev-2025/Knowledge-Weaver
source venv/bin/activate
cd backend_api
nohup uvicorn main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
echo "Backend started on port 8000"

# Start Frontend
cd ../app_dashboard
nohup python3 -m http.server 8080 > ../logs/frontend.log 2>&1 &
echo "Frontend started on port 8080"
