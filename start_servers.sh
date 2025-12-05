#!/bin/bash
# Kill existing servers
pkill -f uvicorn
pkill -f http.server

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
