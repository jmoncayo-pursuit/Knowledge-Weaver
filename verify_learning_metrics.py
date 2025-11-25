import requests
import json
import time
import sys
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def run_test():
    print("🧪 Starting Learning Metrics Verification...")
    
    # 1. Simulate an ingestion with AI correction
    # AI thought it was "Policy", but Human says "Procedure"
    payload = {
        "text": "To reset your password, click the link in the email.",
        "url": "http://help.example.com/password",
        "category": "Procedure", # Human correction
        "tags": ["#it", "#security", "#password"], # Human tags
        "summary": "Password reset instructions",
        "ai_prediction": {
            "category": "Policy", # AI prediction (Wrong)
            "tags": ["#it", "#security"], # AI prediction (Missing #password)
            "summary": "Password policy"
        }
    }
    
    print("📝 Sending Ingestion with Correction...")
    try:
        response = requests.post(f"{API_URL}/ingest", headers=HEADERS, json=payload)
        if response.status_code != 200:
            print(f"❌ Ingestion failed: {response.text}")
            return False
        entry_id = response.json().get("id")
        print(f"✅ Ingestion successful. ID: {entry_id}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

    # 2. Verify Learning Metrics Endpoint
    print("🔍 Checking /api/metrics/learning...")
    time.sleep(1) # Allow for file write
    
    try:
        response = requests.get(f"{API_URL}/metrics/learning?limit=5", headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to fetch metrics: {response.text}")
            return False
            
        events = response.json()
        if not events:
            print("❌ No learning events found")
            return False
            
        # Check if our event is there (most recent)
        latest_event = events[0] # Assuming reverse order
        
        # Verify content
        ai_cat = latest_event["ai_prediction"]["category"]
        human_cat = latest_event["human_correction"]["category"]
        
        if ai_cat == "Policy" and human_cat == "Procedure":
            print("✅ Learning Event Verified: AI 'Policy' -> Human 'Procedure'")
        else:
            print(f"❌ Mismatch in event data: AI={ai_cat}, Human={human_cat}")
            return False
            
        # Cleanup
        requests.delete(f"{API_URL}/knowledge/{entry_id}", headers=HEADERS)
        print("🧹 Test entry deleted.")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
