import requests
import json

API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-secret-key-12345"
HEADERS = {"X-API-Key": API_KEY}

def get_recent_entry():
    try:
        response = requests.get(f"{API_URL}/knowledge/recent?limit=1", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]['id']
    except Exception as e:
        print(f"Error fetching recent: {e}")
    return None

    with open("reproduce_output.txt", "w") as f:
        if entry_id:
            f.write(f"Attempting to reanalyze entry: {entry_id}\n")
            try:
                data = {"summary": "Updated summary for testing"} 
                response = requests.patch(
                    f"{API_URL}/knowledge/{entry_id}?reanalyze=true",
                    headers=HEADERS,
                    json=data
                )
                f.write(f"Status Code: {response.status_code}\n")
                f.write(f"Response: {response.text}\n")
            except Exception as e:
                f.write(f"Error triggering update: {e}\n")
        else:
            f.write("No entries found to test.\n")
