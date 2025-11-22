import requests
import time

# Configuration
API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def verify_deletion():
    print("Starting Deletion Verification...")
    
    # 1. Ingest a test entry
    print("\n1. Ingesting test entry...")
    from datetime import datetime
    ingest_payload = {
        "text": "This is a temporary test entry for deletion verification.",
        "url": "http://test.com/delete-me",
        "timestamp": datetime.now().isoformat(),
        "category": "Test",
        "tags": ["test", "delete"],
        "summary": "Test entry"
    }
    
    response = requests.post(f"{API_URL}/ingest", headers=HEADERS, json=ingest_payload)
    if response.status_code == 200:
        entry_id = response.json()['id']
        print(f"   Success: Ingested entry with ID: {entry_id}")
    else:
        print(f"   Failed to ingest: {response.text}")
        return

    # Wait for ingestion
    time.sleep(1)
    
    # 2. Verify it exists (via recent)
    print("\n2. Verifying entry exists...")
    response = requests.get(f"{API_URL}/knowledge/recent?limit=5", headers=HEADERS)
    if response.status_code == 200:
        recent = response.json()
        found = False
        for entry in recent:
            if entry['id'] == entry_id:
                found = True
                break
        
        if found:
            print("   Success: Entry found in recent list")
        else:
            print("   Failed: Entry not found in recent list")
            return
    else:
        print(f"   Failed to fetch recent: {response.text}")
        return
        
    # 3. Delete the entry
    print(f"\n3. Deleting entry {entry_id}...")
    response = requests.delete(f"{API_URL}/knowledge/{entry_id}", headers=HEADERS)
    
    if response.status_code == 200:
        print("   Success: Delete request successful")
    else:
        print(f"   Failed to delete: {response.text}")
        return
        
    # 4. Verify it is gone
    print("\n4. Verifying entry is gone...")
    time.sleep(1) # Give it a moment
    response = requests.get(f"{API_URL}/knowledge/recent?limit=5", headers=HEADERS)
    if response.status_code == 200:
        recent = response.json()
        found = False
        for entry in recent:
            if entry['id'] == entry_id:
                found = True
                break
        
        if found:
            print("   Failed: Entry still exists in recent list!")
        else:
            print("   SUCCESS: Entry is gone from recent list!")
    else:
        print(f"   Failed to fetch recent: {response.text}")

if __name__ == "__main__":
    verify_deletion()
