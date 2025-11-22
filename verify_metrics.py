import requests
import json

# Configuration
API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def verify_metrics():
    print("Starting Dashboard Metrics Verification...")
    
    try:
        resp = requests.get(f"{API_URL}/metrics/dashboard", headers=HEADERS)
        
        if resp.status_code == 200:
            metrics = resp.json()
            print("Success: Fetched metrics")
            print(json.dumps(metrics, indent=2))
            
            # Assertions
            assert "total_knowledge" in metrics
            assert "verified_count" in metrics
            assert "verified_ratio" in metrics
            assert "query_volume_7d" in metrics
            assert "knowledge_gaps_7d" in metrics
            
            assert metrics["total_knowledge"] >= 0
            assert metrics["verified_count"] >= 0
            assert metrics["verified_count"] <= metrics["total_knowledge"]
            assert 0.0 <= metrics["verified_ratio"] <= 100.0
            
            print("SUCCESS: All metrics present and valid.")
        else:
            print(f"FAILED: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"FAILED: Exception occurred: {e}")

if __name__ == "__main__":
    verify_metrics()
