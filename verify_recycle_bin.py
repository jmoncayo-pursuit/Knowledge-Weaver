import requests
import json
from datetime import datetime
import time

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def verify_recycle_bin():
    print("Starting Recycle Bin Verification...")
    
    # Step A: Ingest a test item
    print("\nStep A: Ingesting test item 'Recycle Bin Test'...")
    ingest_payload = {
        "text": "This is a test entry for the recycle bin functionality.",
        "url": "http://test.com/recycle-bin-test",
        "timestamp": datetime.utcnow().isoformat(),
        "category": "Test",
        "tags": ["#RecycleBinTest"],
        "summary": "Recycle Bin Test Item"
    }
    
    try:
        resp = requests.post(f"{API_URL}/api/v1/ingest", headers=HEADERS, json=ingest_payload)
        if resp.status_code == 200:
            entry_id = resp.json().get("id")
            print(f"   SUCCESS: Ingested entry with ID: {entry_id}")
        else:
            print(f"   FAILED: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Step B: Delete the item via API (Soft Delete)
    print(f"\nStep B: Soft Deleting entry {entry_id}...")
    try:
        resp = requests.delete(f"{API_URL}/api/v1/knowledge/{entry_id}", headers=HEADERS)
        if resp.status_code == 200:
            print(f"   SUCCESS: Deleted entry {entry_id}")
        else:
            print(f"   FAILED: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Step C: Verify item is gone from active search
    print(f"\nStep C: Verifying entry is gone from active search...")
    try:
        search_resp = requests.post(
            f"{API_URL}/api/v1/knowledge/query",
            headers=HEADERS,
            json={"query": "Recycle Bin Test"}
        )
        
        if search_resp.status_code == 200:
            results = search_resp.json().get("results", [])
            found = any(r.get("knowledge_id") == entry_id for r in results)
            
            if not found:
                print(f"   SUCCESS: Entry not found in active search (as expected)")
            else:
                print(f"   FAILED: Entry still visible in search results!")
                return False
        else:
            print(f"   FAILED: Search request failed - {search_resp.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
        
    # Step D: Verify item appears in deleted items list
    print(f"\nStep D: Verifying entry appears in deleted items...")
    try:
        recent_resp = requests.get(
            f"{API_URL}/api/v1/knowledge/recent",
            headers=HEADERS,
            params={"limit": 10, "deleted_only": True}
        )
        
        if recent_resp.status_code == 200:
            entries = recent_resp.json()
            found = any(e.get("id") == entry_id for e in entries)
            
            if found:
                print(f"   SUCCESS: Entry found in deleted items list")
            else:
                print(f"   FAILED: Entry NOT found in deleted items list!")
                return False
        else:
            print(f"   FAILED: Recent items request failed - {recent_resp.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
        
    # Step E: Restore the item
    print(f"\nStep E: Restoring entry {entry_id}...")
    try:
        resp = requests.post(f"{API_URL}/api/v1/knowledge/{entry_id}/restore", headers=HEADERS)
        if resp.status_code == 200:
            print(f"   SUCCESS: Restored entry {entry_id}")
        else:
            print(f"   FAILED: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
        
    # Step F: Verify item is back in active search
    print(f"\nStep F: Verifying entry is back in active search...")
    try:
        # Wait a moment for index update if needed (though usually immediate)
        time.sleep(1)
        search_resp = requests.post(
            f"{API_URL}/api/v1/knowledge/query",
            headers=HEADERS,
            json={"query": "Recycle Bin Test"}
        )
        
        if search_resp.status_code == 200:
            results = search_resp.json().get("results", [])
            found = any(r.get("knowledge_id") == entry_id for r in results)
            
            if found:
                print(f"   SUCCESS: Entry found in active search!")
                print("\n✅ ALL TESTS PASSED - Recycle Bin functionality is working correctly!")
                return True
            else:
                print(f"   FAILED: Entry NOT found in search results after restore!")
                return False
        else:
            print(f"   FAILED: Search request failed - {search_resp.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    success = verify_recycle_bin()
    exit(0 if success else 1)
