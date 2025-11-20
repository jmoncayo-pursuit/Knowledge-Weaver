import requests
import json
from datetime import datetime

def test_ingest():
    url = "http://localhost:8000/api/v1/ingest"
    # 1. Ingest a unique entry
    unique_text = "AI-Native Persistence Test [2025-11-20T01:30:39-05:00]"
    print(f"Ingesting: {unique_text}")
    
    ingest_payload = {
        "text": unique_text,
        "url": "http://internal.wiki/persistence-test",
        "screenshot": None,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # The schema defines 'url', but let's check what I defined in schemas.py
    # class IngestRequest(BaseModel):
    #     text: str
    #     screenshot: Optional[str]
    #     url: str
    #     timestamp: datetime
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "dev-secret-key-12345"
    }
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=ingest_payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("id"):
                print("SUCCESS: Ingestion verified!")
            else:
                print("FAILURE: Invalid response format")
        else:
            print("FAILURE: Request failed")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_ingest()
