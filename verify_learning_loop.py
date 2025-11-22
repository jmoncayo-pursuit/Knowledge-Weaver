import requests
import json
import time

# Configuration
API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def verify_learning_loop():
    print("Starting Active Learning Verification Loop...")
    
    # 1. Baseline Analysis
    print("\n1. Baseline: Analyzing 'The printer is broken'...")
    baseline_payload = {
        "text": "The printer is broken",
        "url": "http://test.com",
        "timestamp": "2023-10-27T10:00:00Z"
    }
    
    try:
        resp = requests.post(f"{API_URL}/analyze", headers=HEADERS, json=baseline_payload)
        if resp.status_code == 200:
            baseline_tags = resp.json().get("tags", [])
            print(f"   Baseline Tags: {baseline_tags}")
        else:
            print(f"   Failed to analyze: {resp.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 2. Teach (Ingest with specific tag)
    print("\n2. Teach: Ingesting 'The printer is broken' with tag '#IT_Hardware_Issue'...")
    ingest_payload = {
        "text": "The printer is broken",
        "url": "http://internal.wiki/printers",
        "timestamp": "2023-10-27T10:00:00Z",
        "category": "IT Support",
        "tags": ["IT_Hardware_Issue"],
        "summary": "Printer malfunction report"
    }
    
    entry_id = None
    try:
        resp = requests.post(f"{API_URL}/ingest", headers=HEADERS, json=ingest_payload)
        if resp.status_code == 200:
            entry_id = resp.json().get("id")
            print(f"   Success: Ingested entry {entry_id}")
        else:
            print(f"   Failed to ingest: {resp.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # Wait a moment for indexing (though Chroma is usually fast)
    time.sleep(1)

    # 3. Verify Training (Analyze similar text)
    print("\n3. Verify: Analyzing 'My printer is not printing'...")
    verify_payload = {
        "text": "My printer is not printing",
        "url": "http://test.com/new",
        "timestamp": "2023-10-27T10:05:00Z"
    }
    
    try:
        resp = requests.post(f"{API_URL}/analyze", headers=HEADERS, json=verify_payload)
        if resp.status_code == 200:
            new_tags = resp.json().get("tags", [])
            print(f"   New Tags: {new_tags}")
            
            if "IT_Hardware_Issue" in new_tags:
                print("   SUCCESS: AI learned the new tag '#IT_Hardware_Issue'!")
            else:
                print("   FAILED: AI did not suggest '#IT_Hardware_Issue'.")
                print("   (Note: This might happen if the model doesn't find the example relevant enough or ignores the few-shot prompt)")
        else:
            print(f"   Failed to analyze: {resp.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Cleanup
    if entry_id:
        print(f"\n4. Cleanup: Deleting entry {entry_id}...")
        requests.delete(f"{API_URL}/knowledge/{entry_id}", headers=HEADERS)

if __name__ == "__main__":
    verify_learning_loop()
