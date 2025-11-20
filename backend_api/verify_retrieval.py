import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def test_ingest_and_retrieve():
    # 1. Skip Ingestion (We are testing persistence of previously ingested data)
    # unique_text = "Backend Fix Verification - Collection Name"
    # print(f"Ingesting: {unique_text}")
    
    # ingest_payload = {
    #     "text": unique_text,
    #     "url": "http://internal.wiki/backend-fix",
    #     "screenshot": None,
    #     "timestamp": datetime.utcnow().isoformat()
    # }
    
    # try:
    #     resp = requests.post(f"{BASE_URL}/ingest", json=ingest_payload, headers=HEADERS)
    #     print(f"Ingest Status: {resp.status_code}")
    #     if resp.status_code != 200:
    #         print(f"Ingest Failed: {resp.text}")
    #         return
            
    #     ingest_data = resp.json()
    #     print(f"Ingest Response: {ingest_data}")
        
    #     # Wait a moment for indexing
    #     time.sleep(1)
        
        # 2. Query for the text
    query = "AI-Native Persistence Test"
    print(f"\nQuerying: {query}")
        
        query_payload = {"query": query}
        resp = requests.post(f"{BASE_URL}/knowledge/query", json=query_payload, headers=HEADERS)
        print(f"Query Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Query Response: {json.dumps(data, indent=2)}")
            
            results = data.get("results", [])
            if results:
                print(f"SUCCESS: Found {len(results)} results.")
                print(f"Top result: {results[0]['content']}")
                print(f"Score: {results[0]['similarity_score']}")
            else:
                print("FAILURE: No results found.")
        else:
            print(f"Query Failed: {resp.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_ingest_and_retrieve()
