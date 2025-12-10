import requests
import base64
import os
import json

# Configuration
API_URL = "http://localhost:8000/api/v1/ingest"
API_KEY = "dev-secret-key-12345" # From env BACKEND_API_KEY
IMAGE_PATH = "/Users/jmoncayopursuit.org/.gemini/antigravity/brain/62676513-6cf9-462b-a3b1-8ea2c3a17248/uploaded_image_1764952252910.png"

def add_entry():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        return

    with open(IMAGE_PATH, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {
        "text": "Discussion about remote work expense policy. Contains PII that needs redaction.",
        "url": "https://teams.microsoft.com/messages/123456",
        "screenshot": encoded_string,
        "category": "Policy",
        "tags": ["remote-work", "expenses", "PII"],
        "summary": "Chat log showing Alice and Bob discussing expense policy for monitors. Contains visible names."
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print("Successfully added PII entry!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed to add entry. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_entry()
