import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"  # Assuming default dev key
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def analyze(text, label):
    print(f"\n--- {label} ---")
    print(f"Analyzing: '{text}'")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            headers=HEADERS,
            json={"text": text, "url": "http://test.com"}
        )
        response.raise_for_status()
        data = response.json()
        tags = data.get("tags", [])
        print(f"Suggested Tags: {tags}")
        return tags
    except Exception as e:
        print(f"Error: {e}")
        return []

def ingest(text, tags):
    print(f"\n--- TEACHING ---")
    print(f"Ingesting: '{text}' with tags: {tags}")
    try:
        response = requests.post(
            f"{BASE_URL}/ingest",
            headers=HEADERS,
            json={
                "text": text,
                "url": "http://test.com",
                "category": "Office Operations",
                "tags": tags,
                "summary": "Report about broken office equipment."
            }
        )
        response.raise_for_status()
        print("Ingestion Successful!")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # 1. Baseline
    baseline_tags = analyze("The coffee machine is broken.", "BASELINE (Before Teaching)")
    
    # 2. Teach
    ingest("The coffee machine is broken.", ["#OfficeOps", "maintenance"])
    
    # Allow a moment for indexing (though Chroma is usually fast)
    time.sleep(1)
    
    # 3. Test
    # Using a slightly different phrase to prove generalization, not just memorization
    test_tags = analyze("The toaster is broken.", "TEST (After Teaching)")
    
    print("\n--- RESULTS ---")
    if "#OfficeOps" in test_tags:
        print("✅ SUCCESS: The AI learned the tag '#OfficeOps'!")
    else:
        print("❌ FAILURE: The AI did not suggest '#OfficeOps'.")

if __name__ == "__main__":
    main()
