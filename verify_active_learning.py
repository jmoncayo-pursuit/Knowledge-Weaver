import urllib.request
import json
import sys
import time

API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"

SCENARIO_TEXT = """
Agent: User needs password reset for legacy system.
Lead: Use the new Spider Protocol. Auth via mobile app first.
Agent: Done. Reset link sent.
"""

def api_request(endpoint, method="GET", data=None):
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    if data:
        json_data = json.dumps(data).encode("utf-8")
    else:
        json_data = None
        
    req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"API Request Failed ({endpoint}): {e}")
        return None

def verify_active_learning():
    print("--- Phase A: Teach (Simulating Capture & Edit) ---")
    
    # 1. Ingest (Capture)
    print("Ingesting Scenario 2...")
    ingest_data = {
        "text": SCENARIO_TEXT,
        "url": "mock_teams_scenario_2",
        "category": "IT Support",
        "tags": ["#password_reset"],
        "summary": "Legacy password reset"
    }
    result = api_request("/ingest", "POST", ingest_data)
    if not result or "id" not in result:
        print("❌ Ingest failed")
        sys.exit(1)
    
    entry_id = result["id"]
    print(f"Entry Created: {entry_id}")
    
    # 2. Edit (Teach)
    print("Teaching: Updating tags to #SpiderProtocol_Auth...")
    edit_data = {
        "tags": ["#SpiderProtocol_Auth"],
        "category": "IT Support",
        "summary": "Legacy password reset via Spider Protocol"
    }
    # Using PATCH to update
    update_res = api_request(f"/knowledge/{entry_id}", "PATCH", edit_data)
    if not update_res:
        print("❌ Update failed")
        sys.exit(1)
        
    print("✅ Teaching Complete. Waiting for vector store update...")
    time.sleep(2) 

    print("\n--- Phase B: Verify (Analyze New Content) ---")
    
    # 3. Analyze (Verify)
    print("Analyzing same text again...")
    analyze_data = {
        "text": SCENARIO_TEXT,
        "url": "mock_teams_scenario_2_retry"
    }
    
    analysis = api_request("/analyze", "POST", analyze_data)
    
    if not analysis:
        print("❌ Analysis failed")
        sys.exit(1)
        
    suggested_tags = analysis.get("tags", [])
    print(f"AI Suggested Tags: {suggested_tags}")
    
    if "#SpiderProtocol_Auth" in suggested_tags:
        print("✅ SUCCESS: AI learned #SpiderProtocol_Auth")
    else:
        print(f"❌ FAILURE: AI did not suggest #SpiderProtocol_Auth. Got: {suggested_tags}")
        sys.exit(1)

if __name__ == "__main__":
    verify_active_learning()
