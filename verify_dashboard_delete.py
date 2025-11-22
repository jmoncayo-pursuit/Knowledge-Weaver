import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def verify_dashboard_delete():
    print("Starting Dashboard Delete Verification...")
    
    # Step A: Ingest a test item
    print("\nStep A: Ingesting test item 'To Be Deleted'...")
    ingest_payload = {
        "text": "This is a test entry that should be deleted.",
        "url": "http://test.com/delete-test",
        "timestamp": datetime.utcnow().isoformat(),
        "category": "Test",
        "tags": ["#DeleteTest"],
        "summary": "To Be Deleted"
    }
    
    try:
        resp = requests.post(f"{API_URL}/api/v1/ingest", headers=HEADERS, json=ingest_payload)
        if resp.status_code == 200:
            entry_id = resp.json().get("id")
            print(f"   SUCCESS: Ingested entry with ID: {entry_id}")
        else:
            print(f"   FAILED: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Step B: Delete the item via API
    print(f"\nStep B: Deleting entry {entry_id} via DELETE API...")
    try:
        resp = requests.delete(f"{API_URL}/api/v1/knowledge/{entry_id}", headers=HEADERS)
        if resp.status_code == 200:
            print(f"   SUCCESS: Deleted entry {entry_id}")
        else:
            print(f"   FAILED: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Step C: Verify the item is gone
    print(f"\nStep C: Verifying entry {entry_id} is gone...")
    try:
        # Search for the entry to confirm it's deleted
        search_resp = requests.post(
            f"{API_URL}/api/v1/knowledge/query",
            headers=HEADERS,
            json={"query": "To Be Deleted"}
        )
        
        if search_resp.status_code == 200:
            results = search_resp.json().get("results", [])
            # Check if our entry is in the results
            found = any(r.get("knowledge_id") == entry_id for r in results)
            
            if not found:
                print(f"   SUCCESS: Entry {entry_id} is confirmed deleted!")
                print("\n✅ ALL TESTS PASSED - Delete functionality is working correctly!")
                return True
            else:
                print(f"   FAILED: Entry {entry_id} still exists in search results!")
                return False
        else:
            print(f"   FAILED: Search request failed - {search_resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    success = verify_dashboard_delete()
    exit(0 if success else 1)
