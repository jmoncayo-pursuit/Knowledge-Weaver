import requests
import base64
import json
import os

def test_redaction():
    with open("debug_output.txt", "w") as log:
        log.write("Starting test...\n")
    print("Starting test...")
    url = "http://localhost:8002/api/v1/redact"
    file_path = "test_screenshot.png"
    
    if not os.path.exists(file_path):
        print("Test image not found!")
        return

    print(f"Sending {file_path} to {url}...")
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        # Add API key header if needed (using default from env or mock)
        headers = {"X-API-Key": os.getenv("KIRO_API_KEY", "dev-secret-key-12345")} 
        
        try:
            response = requests.post(url, files=files, headers=headers)
            
            if response.status_code == 200:
                print("Success!")
                data = response.json()
                print("Redacted Items:", json.dumps(data.get("redacted_items"), indent=2))
                
                # Save redacted image
                redacted_b64 = data.get("redacted_image", "").split(",")[1]
                with open("redacted_result.png", "wb") as out:
                    out.write(base64.b64decode(redacted_b64))
                print("Saved redacted_result.png")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_redaction()
