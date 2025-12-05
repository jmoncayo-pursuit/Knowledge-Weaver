import time
import requests
import os
import sys

BACKEND_URL = "http://localhost:8000/health"
FRONTEND_URL = "http://localhost:8080"
LOG_FILE = "logs/server.log"

def check_health():
    try:
        response = requests.get(BACKEND_URL, timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"Health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Health check failed: {e}")
        return False

def diagnose():
    print("\n--- DIAGNOSTICS ---")
    if not os.path.exists(LOG_FILE):
        print(f"Log file {LOG_FILE} not found.")
        return

    print(f"Reading last 20 lines of {LOG_FILE}...")
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-20:] if len(lines) > 20 else lines
            for line in last_lines:
                print(line.strip())
    except Exception as e:
        print(f"Error reading log file: {e}")

def main():
    print("Starting Watcher...")
    while True:
        if not check_health():
            print("Server appears down or unhealthy.")
            diagnose()
            # In a real self-heal scenario, we might trigger a restart here.
            # For now, we just report.
            # os.system("./run_dev.sh") 
        else:
            # print("Server is healthy.")
            pass
        
        time.sleep(30)

if __name__ == "__main__":
    # If run with 'diagnose' argument, just run diagnostics once
    if len(sys.argv) > 1 and sys.argv[1] == "diagnose":
        diagnose()
    else:
        main()
