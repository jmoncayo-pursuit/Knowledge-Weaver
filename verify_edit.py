import requests
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def verify_edit():
    print("Starting Inline Edit Verification...")
    
    # 1. Ingest Unverified Entry (simulated)
    # We'll use /ingest but it defaults to verified_human. 
    # We can't easily force it to be unverified via public API without changing /ingest.
    # However, we can check if the update works and sets it to verified_human (even if it already was).
    # To be more rigorous, we could try to find an unverified entry first.
    
    print("\n1. Ingesting test entry...")
    payload = {
        "text": "The cafeteria serves pizza on Fridays.",
        "url": "http://internal.com/food",
        "timestamp": datetime.now().isoformat(),
        "category": "Uncategorized",
        "tags": ["food"],
        "summary": "Food info"
    }
    
    resp = requests.post(f"{API_URL}/ingest", headers=HEADERS, json=payload)
    if resp.status_code != 200:
        print(f"   Failed to ingest: {resp.text}")
        return
        
    entry_id = resp.json()['id']
    print(f"   Success: Ingested entry {entry_id}")
    
    # 2. Verify initial state
    # We can't easily get a single entry by ID via public API (except search).
    # We'll assume it's there.
    
    # 3. Update Entry (PATCH)
    print("\n2. Updating entry (Category -> 'Culture', Tags -> 'food, friday')...")
    update_payload = {
        "category": "Culture",
        "tags": ["food", "friday"],
        "summary": "Friday pizza tradition"
    }
    
    resp_patch = requests.patch(f"{API_URL}/knowledge/{entry_id}", headers=HEADERS, json=update_payload)
    
    if resp_patch.status_code == 200:
        print("   Success: Update request accepted.")
    else:
        print(f"   Failed to update: {resp_patch.text}")
        return
        
    time.sleep(2) # Wait for consistency
    
    # 4. Verify Update & Verification Status
    print("\n3. Verifying update via Search...")
    # Search for the unique text
    query = "cafeteria pizza friday"
    resp_search = requests.post(f"{API_URL}/knowledge/query", headers=HEADERS, json={"query": query})
    
    if resp_search.status_code == 200:
        results = resp_search.json()['results']
        found = False
        for r in results:
            if r['knowledge_id'] == entry_id:
                found = True
                meta = r['metadata']
                print(f"   Found entry:")
                print(f"   - Category: {meta.get('category')} (Expected: Culture)")
                print(f"   - Tags: {meta.get('tags')} (Expected: food, friday)")
                print(f"   - Status: {meta.get('verification_status')} (Expected: verified_human)")
                
                if (meta.get('category') == 'Culture' and 
                    'friday' in meta.get('tags') and 
                    meta.get('verification_status') == 'verified_human'):
                    print("   SUCCESS: Entry updated and verified!")
                else:
                    print("   FAILED: Metadata mismatch.")
                break
        
        if not found:
            print("   FAILED: Could not find entry after update.")
    else:
        print(f"   Failed to search: {resp_search.text}")

    # Cleanup
    requests.delete(f"{API_URL}/knowledge/{entry_id}", headers=HEADERS)

if __name__ == "__main__":
    verify_edit()
