"""
One-time ingestion script to load sample chat logs into Knowledge-Weaver
"""
import json
import requests
import sys

# Configuration
API_URL = "http://localhost:8000/api/v1/chat-logs/process"
API_KEY = "dev-secret-key-12345"
SAMPLE_DATA_PATH = "../sample_chat_logs.json"

def load_sample_data():
    """Load sample chat logs from JSON file"""
    try:
        with open(SAMPLE_DATA_PATH, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data)} chat messages from {SAMPLE_DATA_PATH}")
        return data
    except FileNotFoundError:
        print(f"✗ Error: Could not find {SAMPLE_DATA_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in {SAMPLE_DATA_PATH}: {e}")
        sys.exit(1)

def ingest_data(chat_logs):
    """Send chat logs to the backend API for processing"""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "chat_logs": chat_logs
    }
    
    print(f"\nSending {len(chat_logs)} messages to {API_URL}...")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✓ Ingestion successful!")
        print(f"  - Success count: {result.get('success_count', 0)}")
        print(f"  - Failed count: {result.get('failed_count', 0)}")
        print(f"  - Processed IDs: {len(result.get('processed_ids', []))}")
        
        if result.get('errors'):
            print(f"\n⚠ Errors encountered:")
            for error in result['errors']:
                print(f"  - {error}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Error: Could not connect to backend at {API_URL}")
        print("  Make sure the backend server is running (python main.py)")
        return False
    except requests.exceptions.Timeout:
        print(f"\n✗ Error: Request timed out")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        if response.status_code == 401:
            print("  Authentication failed - check API key")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

def main():
    print("=" * 60)
    print("Knowledge-Weaver Sample Data Ingestion")
    print("=" * 60)
    
    # Load sample data
    chat_logs = load_sample_data()
    
    # Ingest data
    success = ingest_data(chat_logs)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Sample data ingestion complete!")
        print("=" * 60)
        print("\nYour knowledge base is now populated with sample data.")
        print("You can now:")
        print("  - Query the knowledge base via the Chrome Extension")
        print("  - View metrics in the Leadership Dashboard")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ Ingestion failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
