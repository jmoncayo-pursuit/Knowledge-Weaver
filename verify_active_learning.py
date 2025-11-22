import requests
import json
import time
import os

# Configuration
API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def verify_active_learning():
    print("Starting Active Learning Verification...")
    
    # 1. Ingest a "verified_human" entry with a specific category
    print("\n1. Ingesting verified example...")
    verified_text = "Agent: Member wants to add newborn. Baby born 2 days ago. Lead: Send QLE form. Must be done within 31 days."
    verified_category = "Special Protocol: Newborn"
    
    ingest_payload = {
        "text": verified_text,
        "url": "http://test.com/verified",
        "timestamp": "2023-10-27T10:00:00Z",
        "category": verified_category,
        "tags": ["newborn", "qle"],
        "summary": "Newborn addition protocol",
        "screenshot": None
    }
    
    response = requests.post(f"{API_URL}/ingest", headers=HEADERS, json=ingest_payload)
    if response.status_code == 200:
        print(f"   Success: Ingested verified entry with category '{verified_category}'")
    else:
        print(f"   Failed to ingest: {response.text}")
        return

    # Wait for ingestion to settle (though it should be immediate with Chroma)
    time.sleep(1)
    
    # 2. Analyze a new, similar text
    print("\n2. Analyzing similar text...")
    new_text = "Agent: Employee just had a baby yesterday. Needs to add to plan. Lead: Standard QLE process applies."
    
    analyze_payload = {
        "text": new_text,
        "url": "http://test.com/new",
        "timestamp": "2023-10-27T11:00:00Z"
    }
    
    response = requests.post(f"{API_URL}/analyze", headers=HEADERS, json=analyze_payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Analysis Result:")
        print(f"   Category: {result['category']}")
        print(f"   Tags: {result['tags']}")
        print(f"   Summary: {result['summary']}")
        
        # 3. Verification
        # We hope the category is influenced by the verified example
        if result['category'] == verified_category:
            print(f"\nSUCCESS: The AI used the verified category '{verified_category}'!")
        else:
            print(f"\nPARTIAL SUCCESS: Analysis worked, but category '{result['category']}' differs from verified '{verified_category}'.")
            print("This is expected if the model decides the new text doesn't perfectly match the example, but check logs to ensure context was passed.")
            
    else:
        print(f"   Failed to analyze: {response.text}")

if __name__ == "__main__":
    verify_active_learning()
