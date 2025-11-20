import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "dev-secret-key-12345"
}

def test_analyze():
    print("Testing /analyze endpoint...")
    
    payload = {
        "text": "The new remote work policy allows 2 days of WFH per week. Employees must be in the office Tue-Thu.",
        "url": "http://internal.wiki/remote-work",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        print(f"Sending request to {BASE_URL}/analyze...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/analyze", json=payload, headers=HEADERS, timeout=60)
        duration = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Duration: {duration:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("\nAnalysis Result:")
            print(json.dumps(data, indent=2))
            
            # Validate fields
            if "category" in data and "tags" in data and "summary" in data:
                print("\nSUCCESS: Analysis returned expected fields.")
            else:
                print("\nFAILURE: Missing fields in response.")
        else:
            print(f"\nFAILURE: Request failed with {response.text}")
            
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    test_analyze()
