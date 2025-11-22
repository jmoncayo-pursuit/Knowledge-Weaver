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

def verify_filter():
    print("Starting Verified Filter Verification...")
    
    # 1. Ingest Verified Entry
    print("\n1. Ingesting VERIFIED entry...")
    verified_payload = {
        "text": "The official company policy for remote work requires 3 days in office.",
        "url": "http://policy.com/remote",
        "timestamp": datetime.now().isoformat(),
        "category": "Policy",
        "tags": ["remote", "policy", "verified_test"],
        "summary": "Verified remote work policy"
    }
    
    # Note: The /ingest endpoint automatically sets verification_status="verified_human"
    # So this entry will be verified.
    resp_v = requests.post(f"{API_URL}/ingest", headers=HEADERS, json=verified_payload)
    if resp_v.status_code == 200:
        verified_id = resp_v.json()['id']
        print(f"   Success: Ingested verified entry: {verified_id}")
    else:
        print(f"   Failed to ingest verified: {resp_v.text}")
        return

    # 2. Ingest Unverified Entry (We need to manually insert one or simulate it)
    # Since /ingest defaults to verified_human, we might need to hack it or just use an existing one if we can't control it.
    # Wait, I can't easily create an unverified entry via the public API if it hardcodes "verified_human".
    # Let's check api.py again.
    # It sets "verification_status": "verified_human".
    # To test the filter, I need an unverified entry.
    # I will use the /chat-logs/process endpoint which creates entries from chat logs.
    # These usually have a different status or I can assume they are "unverified" or "auto_generated".
    # Let's check chat_processor.py or just assume chat logs are not "verified_human".
    
    print("\n2. Ingesting UNVERIFIED entry (via chat log processing)...")
    chat_log_payload = {
        "chat_logs": [
            {
                "id": "msg_unverified_1",
                "timestamp": datetime.now().isoformat(),
                "sender": "User1",
                "content": "I think the remote work policy is 2 days in office, but I'm not sure.",
                "metadata": {"thread_id": "t1"}
            }
        ]
    }
    
    # This endpoint processes logs and adds them to vector db.
    # I need to ensure it actually adds something.
    resp_u = requests.post(f"{API_URL}/chat-logs/process", headers=HEADERS, json=chat_log_payload)
    if resp_u.status_code == 200:
        print(f"   Success: Processed chat log. Result: {resp_u.json()}")
    else:
        print(f"   Failed to process chat log: {resp_u.text}")
        # Proceeding anyway, maybe there are other unverified entries
        
    time.sleep(2) # Wait for indexing
    
    # 3. Search WITHOUT filter
    print("\n3. Searching WITHOUT filter...")
    query = "remote work policy days in office"
    resp_all = requests.post(f"{API_URL}/knowledge/query", headers=HEADERS, json={"query": query, "verified_only": False})
    
    if resp_all.status_code == 200:
        results = resp_all.json()['results']
        print(f"   Found {len(results)} results.")
        for r in results:
            status = r['metadata'].get('verification_status', 'unknown')
            print(f"   - {r['content'][:50]}... [{status}]")
    else:
        print(f"   Failed search: {resp_all.text}")
        return

    # 4. Search WITH filter
    print("\n4. Searching WITH filter (verified_only=True)...")
    resp_filtered = requests.post(f"{API_URL}/knowledge/query", headers=HEADERS, json={"query": query, "verified_only": True})
    
    if resp_filtered.status_code == 200:
        results = resp_filtered.json()['results']
        print(f"   Found {len(results)} results.")
        all_verified = True
        for r in results:
            status = r['metadata'].get('verification_status', 'unknown')
            print(f"   - {r['content'][:50]}... [{status}]")
            if status != 'verified_human':
                all_verified = False
        
        if all_verified and len(results) > 0:
            print("   SUCCESS: Only verified entries returned.")
        elif len(results) == 0:
             print("   WARNING: No results found with filter.")
        else:
            print("   FAILED: Unverified entries found in filtered results!")
    else:
        print(f"   Failed search: {resp_filtered.text}")

    # Cleanup verified entry
    requests.delete(f"{API_URL}/knowledge/{verified_id}", headers=HEADERS)

if __name__ == "__main__":
    verify_filter()
