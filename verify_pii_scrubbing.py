import requests
import json
import time
import sys

# Configuration
API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def run_test():
    print("🧪 Starting PII Scrubbing Verification...")
    
    # 1. Define input with PII
    pii_text = "Patient John Doe (phone: 555-123-4567, email: john.doe@example.com) has a severe allergy."
    print(f"📝 Input Text: {pii_text}")
    
    payload = {
        "text": pii_text,
        "url": "http://test-pii.com",
        "category": "Test",
        "tags": ["#test", "#pii"],
        "summary": "Test entry with PII"
    }
    
    # 2. Ingest
    try:
        response = requests.post(f"{API_URL}/ingest", headers=HEADERS, json=payload)
        if response.status_code != 200:
            print(f"❌ Ingestion failed: {response.text}")
            return False
            
        entry_id = response.json().get("id")
        print(f"✅ Ingestion successful. ID: {entry_id}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
        
    # 3. Verify Storage (Wait a moment for indexing if async, though here it's sync)
    time.sleep(1)
    
    try:
        # Fetch recent knowledge to find our entry
        response = requests.get(f"{API_URL}/knowledge/recent?limit=5", headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to fetch recent knowledge: {response.text}")
            return False
            
        entries = response.json()
        target_entry = next((e for e in entries if e["id"] == entry_id), None)
        
        if not target_entry:
            print("❌ Created entry not found in recent list")
            return False
            
        stored_text = target_entry["document"] # or 'content' depending on schema mapping in response
        # The response model for recent entries is list of dicts, usually matching internal structure
        # Let's check what 'document' field holds.
        
        print(f"🔍 Stored Text: {stored_text}")
        
        # 4. Assertions
        if "555-123-4567" in stored_text:
            print("❌ Phone number NOT redacted!")
            return False
            
        if "john.doe@example.com" in stored_text:
            print("❌ Email NOT redacted!")
            return False
            
        if "[PHONE_REDACTED]" in stored_text and "[EMAIL_REDACTED]" in stored_text:
            print("✅ PII successfully redacted!")
            
            # Cleanup
            requests.delete(f"{API_URL}/knowledge/{entry_id}", headers=HEADERS)
            print("🧹 Test entry deleted.")
            return True
        else:
            print("⚠️ Redaction markers not found (or partial failure).")
            return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
