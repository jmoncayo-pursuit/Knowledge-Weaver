
import urllib.request
import json
import sys
import time

API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"

def verify_recycle_bin():
    print("--- Verifying Recycle Bin API ---")
    
    # 1. Get a recent entry to delete
    print("Fetching recent entry...")
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/recent?limit=1",
            headers={"X-API-Key": API_KEY}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if not data:
                print("No entries found to delete.")
                sys.exit(1)
            entry_id = data[0]['id']
            print(f"Target Entry ID: {entry_id}")
            
    except Exception as e:
        print(f"Failed to fetch entry: {e}")
        sys.exit(1)

    # 2. Delete the entry
    print(f"Deleting entry {entry_id}...")
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/{entry_id}",
            headers={"X-API-Key": API_KEY},
            method='DELETE'
        )
        with urllib.request.urlopen(req) as response:
            print(f"Delete Status: {response.status}")
            
    except Exception as e:
        print(f"Delete Failed: {e}")
        sys.exit(1)
        
    # 3. Verify it's in the Recycle Bin
    print("Verifying entry is in Recycle Bin...")
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/recent?limit=10&deleted_only=true",
            headers={"X-API-Key": API_KEY}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            deleted_entry = next((e for e in data if e['id'] == entry_id), None)
            
            if deleted_entry:
                print("✅ SUCCESS: Entry found in Recycle Bin.")
            else:
                print("❌ FAILURE: Entry NOT found in Recycle Bin.")
                sys.exit(1)
                
    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)

    # 4. Restore the entry
    print(f"Restoring entry {entry_id}...")
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/{entry_id}/restore",
            headers={"X-API-Key": API_KEY},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            print(f"Restore Status: {response.status}")
            
    except Exception as e:
        print(f"Restore Failed: {e}")
        sys.exit(1)

    # 5. Verify it's back in Active Knowledge
    print("Verifying entry is back in Active Knowledge...")
    try:
        req = urllib.request.Request(
            f"{API_BASE_URL}/knowledge/recent?limit=10",
            headers={"X-API-Key": API_KEY}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            active_entry = next((e for e in data if e['id'] == entry_id), None)
            
            if active_entry:
                print("✅ SUCCESS: Entry restored to Active Knowledge.")
            else:
                print("❌ FAILURE: Entry NOT found in Active Knowledge.")
                sys.exit(1)
                
    except Exception as e:
        print(f"Final Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_recycle_bin()
