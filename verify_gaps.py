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

def verify_gaps():
    print("Starting Knowledge Gaps Verification...")
    
    # 1. Generate some failed queries
    print("\n1. Generating failed queries...")
    failed_queries = [
        "how to teleport to mars",
        "how to teleport to mars", 
        "how to teleport to mars",
        "recipe for invisibility potion",
        "recipe for invisibility potion"
    ]
    
    for q in failed_queries:
        try:
            requests.post(f"{API_URL}/knowledge/query", headers=HEADERS, json={"query": q})
            # time.sleep(0.1) 
        except Exception as e:
            print(f"   Error sending query: {e}")
            
    # 2. Fetch Dashboard Metrics
    print("\n2. Fetching Dashboard Metrics...")
    try:
        resp = requests.get(f"{API_URL}/metrics/dashboard", headers=HEADERS)
        
        if resp.status_code == 200:
            metrics = resp.json()
            recent_gaps = metrics.get("recent_gaps", [])
            
            print(f"   Found {len(recent_gaps)} gaps.")
            print(json.dumps(recent_gaps, indent=2))
            
            # Assertions
            found_teleport = False
            found_invisibility = False
            
            for gap in recent_gaps:
                if "teleport to mars" in gap['query']:
                    found_teleport = True
                    if gap['count'] >= 3:
                        print("   SUCCESS: 'teleport to mars' found with correct count.")
                    else:
                        print(f"   WARNING: 'teleport to mars' count is {gap['count']} (expected >= 3).")
                
                if "invisibility potion" in gap['query']:
                    found_invisibility = True
                    if gap['count'] >= 2:
                        print("   SUCCESS: 'invisibility potion' found with correct count.")
                    else:
                        print(f"   WARNING: 'invisibility potion' count is {gap['count']} (expected >= 2).")
            
            if found_teleport and found_invisibility:
                print("SUCCESS: All simulated gaps found!")
            else:
                print("FAILED: Missing simulated gaps.")
                
        else:
            print(f"FAILED: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"FAILED: Exception occurred: {e}")

if __name__ == "__main__":
    verify_gaps()
