
import urllib.request
import json
import base64
import sys

API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"

def verify_screenshot_upload():
    print("--- Verifying Screenshot Upload ---")
    
    # 1. Get a recent entry ID
    print("Fetching recent entry...")
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/recent?limit=1",
            headers={"X-API-Key": API_KEY}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if not data:
                print("No entries found to update.")
                sys.exit(1)
            entry_id = data[0]['id']
            print(f"Target Entry ID: {entry_id}")
            
    except Exception as e:
        print(f"Failed to fetch entry: {e}")
        sys.exit(1)

    # 2. Create dummy base64 image
    dummy_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    # 3. Send PATCH request with screenshot
    print("Sending PATCH request with screenshot...")
    payload = {
        "screenshot": dummy_image
    }
    
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/{entry_id}",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            method='PATCH'
        )
        with urllib.request.urlopen(req) as response:
            print(f"Update Status: {response.status}")
            
    except Exception as e:
        print(f"Update Failed: {e}")
        sys.exit(1)
        
    # 4. Verify update
    print("Verifying update...")
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/recent?limit=1",
            headers={"X-API-Key": API_KEY}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            updated_entry = next((e for e in data if e['id'] == entry_id), None)
            
            if updated_entry and updated_entry['metadata'].get('has_screenshot'):
                print("✅ SUCCESS: Entry updated with screenshot flag.")
            else:
                print("❌ FAILURE: Screenshot flag not found.")
                sys.exit(1)
                
    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_screenshot_upload()
