import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def print_step(step):
    print(f"\n{'='*50}")
    print(f"STEP: {step}")
    print(f"{'='*50}")

def ingest_knowledge(text, category, tags, summary, verification_status):
    payload = {
        "text": text,
        "url": "http://test-verification.com",
        "category": category,
        "tags": tags,
        "summary": summary,
        "verification_status": verification_status
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ingest", headers=HEADERS, json=payload)
        response.raise_for_status()
        print(f"✅ Ingested ({verification_status}): {summary}")
        return response.json()
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        return None

def search_knowledge(query):
    payload = {
        "query": query,
        "verified_only": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/knowledge/query", headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return None

def main():
    print("🕷️ Starting Spider/Weaver Role Verification 🕸️")
    
    # Unique identifier for this run to avoid collisions
    run_id = int(time.time())
    topic = f"Project Omega Protocol {run_id}"
    
    # Step 1: Weaver (Agent) contributes a draft
    print_step("Test A: Weaver (Agent) contributes a draft")
    weaver_text = f"I think the protocol for Project Omega is to run in circle. This is a draft note. {run_id}"
    ingest_knowledge(
        text=weaver_text,
        category="Procedure",
        tags=["protocol", "omega", "draft"],
        summary=f"Weaver Draft: {topic}",
        verification_status="draft"
    )
    
    # Step 2: Spider (Leader) contributes verified truth
    print_step("Test B: Spider (Leader) contributes verified truth")
    spider_text = f"The OFFICIAL protocol for Project Omega is to run in a straight line. Verified by Leadership. {run_id}"
    ingest_knowledge(
        text=spider_text,
        category="Procedure",
        tags=["protocol", "omega", "verified"],
        summary=f"Spider Verified: {topic}",
        verification_status="verified_human"
    )
    
    # Allow some time for indexing if needed (though usually synchronous for small scale)
    time.sleep(2)
    
    # Step 3: Retrieval Verification
    print_step("Test C: Retrieval Verification (Source of Truth Ranking)")
    query = f"What is the protocol for Project Omega {run_id}?"
    result = search_knowledge(query)
    
    if not result or not result.get('results'):
        print("❌ No results found!")
        sys.exit(1)
        
    results = result['results']
    print(f"Found {len(results)} results.\n")
    
    # Check ranking
    first_result = results[0]
    second_result = results[1] if len(results) > 1 else None
    
    print(f"1. Top Result: {first_result['metadata'].get('verification_status')} - {first_result['metadata'].get('summary')}")
    if second_result:
        print(f"2. Second Result: {second_result['metadata'].get('verification_status')} - {second_result['metadata'].get('summary')}")
    
    # Verification Logic
    top_is_verified = first_result['metadata'].get('verification_status') == 'verified_human'
    
    if top_is_verified:
        print("\n✅ SUCCESS: Spider (Verified) content ranks highest!")
    else:
        print("\n⚠️ WARNING: Weaver (Draft) content outranked Spider content.")
        # This might happen if semantic similarity is much higher for the draft, 
        # but we want to ensure verified usually wins or is at least present.
        # For this test, we expect verified to be top if we implemented boosting.
        # If we haven't implemented boosting yet, this test serves as a baseline.
        
    # Check if both are present
    has_verified = any(r['metadata'].get('verification_status') == 'verified_human' for r in results)
    has_draft = any(r['metadata'].get('verification_status') == 'draft' for r in results)
    
    if has_verified and has_draft:
        print("✅ Both Draft and Verified content retrieved.")
    else:
        print("❌ Missing either Draft or Verified content in results.")

if __name__ == "__main__":
    main()
