import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"

def test_scenario(name, text, expected_category_keyword):
    print(f"\n--- Testing Scenario: {name} ---")
    
    payload = {
        "text": text,
        "url": "http://test-scenario",
        "timestamp": "2025-11-20T12:00:00Z"
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analyze", json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            category = result.get("category", "")
            print(f"Result Category: {category}")
            print(f"Result Summary: {result.get('summary')}")
            
            if expected_category_keyword.lower() in category.lower():
                print("✅ SUCCESS: Category matches expected keyword.")
                return True
            else:
                print(f"❌ FAILURE: Category '{category}' does not contain '{expected_category_keyword}'.")
                return False
        else:
            print(f"❌ FAILURE: API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    # Scenario 1: Deadline Passed
    text1 = """
    Agent: I have an EE who sent their marriage certificate today, but the wedding was 45 days ago. Can we process?
    Lead: No. QLE Policy is strict: documentation must be received within 31 days of the event. No exceptions. The request is denied.
    """
    
    # Scenario 3: Permission to Speak
    text3 = """
    Agent: I have the employee's spouse on the line asking about their dental coverage. The employee is at work and can't talk.
    Lead: Do NOT discuss coverage unless they are listed as an Authorized Representative on the account. Check the 'Profile' tab. If not listed, advise them we need the EE to call in to grant permission first.
    """
    
    success1 = test_scenario("Deadline Passed", text1, "Denied")
    success3 = test_scenario("Permission to Speak", text3, "Compliance")
    
    if success1 and success3:
        print("\n✅ ALL SCENARIOS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME SCENARIOS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
