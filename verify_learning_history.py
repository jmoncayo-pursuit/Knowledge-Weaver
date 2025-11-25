
import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"

def verify_learning_history():
    print("--- Verifying Learning History ---")
    
    # 1. Simulate Ingestion with Correction
    payload = {
        "text": "The printer is out of toner.",
        "url": "verification_script",
        "category": "Office Supplies",
        "tags": ["#OfficeOps", "#Supplies"],
        "summary": "Printer toner issue",
        "ai_prediction": {
            "category": "Equipment",
            "tags": ["#Equipment", "#Broken"],
            "summary": "Printer issue"
        }
    }
    
    print(f"Sending Ingest Request with Correction...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/ingest",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            print(f"Ingestion Status: {response.status}")
            print("Ingestion Successful!")
            
    except urllib.error.HTTPError as e:
        print(f"Ingestion Failed: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
        sys.exit(1)
    except Exception as e:
        print(f"Ingestion Failed: {e}")
        sys.exit(1)
        
    # 2. Fetch Learning History
    print("Fetching Learning History...")
    time.sleep(1) # Give it a moment to write
    
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/metrics/learning",
            headers={"X-API-Key": API_KEY}
        )
        with urllib.request.urlopen(req) as response:
            history = json.loads(response.read().decode('utf-8'))
        
        print(f"History Items: {len(history)}")
        
        if len(history) > 0:
            latest = history[0] # Assuming API returns latest first? Or check logic.
            # My API logic: "for line in reversed(lines):" so yes, latest first.
            
            print(f"Latest Event: {json.dumps(latest, indent=2)}")
            
            # Verify content
            if "#Supplies" in latest['human_correction']['tags']:
                print("✅ SUCCESS: Learning event logged correctly!")
            else:
                print("❌ FAILURE: Logged event does not match expected correction.")
                sys.exit(1)
        else:
            print("❌ FAILURE: No learning history found.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Fetch Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_learning_history()
