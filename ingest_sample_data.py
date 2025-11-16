#!/usr/bin/env python3
"""
One-time ingestion script to populate the Knowledge-Weaver database
with sample chat logs from sample_chat_logs.json
"""
import json
import requests
import sys
from datetime import datetime
from typing import List, Dict

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
API_KEY = "dev-secret-key-12345"
SAMPLE_DATA_FILE = "sample_chat_logs.json"


def load_sample_data(file_path: str) -> List[Dict]:
    """Load sample chat logs from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data)} messages from {file_path}")
        return data
    except FileNotFoundError:
        print(f"✗ Error: File '{file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in '{file_path}': {e}")
        sys.exit(1)


def format_chat_logs(raw_logs: List[Dict]) -> List[Dict]:
    """
    Format raw chat logs to match the ChatMessage schema
    Adds 'platform' field and ensures proper structure
    """
    formatted_logs = []
    for log in raw_logs:
        formatted_log = {
            "id": log["id"],
            "timestamp": log["timestamp"],
            "sender": log["sender"],
            "content": log["content"],
            "platform": "teams",  # Default platform
            "thread_id": None,
            "metadata": {}
        }
        formatted_logs.append(formatted_log)
    
    return formatted_logs


def check_backend_health() -> bool:
    """Check if backend API is running and healthy"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Backend is healthy (status: {health_data.get('status')})")
            print(f"  Vector DB: {health_data.get('vector_db')}")
            return True
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Error: Cannot connect to backend at {BACKEND_URL}")
        print("  Make sure the backend is running:")
        print("  cd backend_api && uvicorn main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"✗ Error checking backend health: {e}")
        return False


def ingest_chat_logs(chat_logs: List[Dict]) -> bool:
    """
    Send chat logs to the backend API for processing
    Handles batching if needed (max 100 messages per batch)
    """
    endpoint = f"{BACKEND_URL}/api/v1/chat-logs/process"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Process in batches of 100
    batch_size = 100
    total_success = 0
    total_failed = 0
    all_errors = []
    
    for i in range(0, len(chat_logs), batch_size):
        batch = chat_logs[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(chat_logs) + batch_size - 1) // batch_size
        
        print(f"\n📤 Sending batch {batch_num}/{total_batches} ({len(batch)} messages)...")
        
        payload = {
            "chat_logs": batch
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=60  # Allow up to 60 seconds for processing
            )
            
            if response.status_code == 200:
                result = response.json()
                success_count = result.get("success_count", 0)
                failed_count = result.get("failed_count", 0)
                errors = result.get("errors", [])
                
                total_success += success_count
                total_failed += failed_count
                all_errors.extend(errors)
                
                print(f"  ✓ Batch processed: {success_count} succeeded, {failed_count} failed")
                
                if errors:
                    print(f"  ⚠ Errors in batch:")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"    - {error}")
                    if len(errors) > 3:
                        print(f"    ... and {len(errors) - 3} more errors")
            
            elif response.status_code == 401:
                print(f"  ✗ Authentication failed: Invalid API key")
                return False
            
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"  ✗ Bad request: {error_detail}")
                return False
            
            else:
                print(f"  ✗ Request failed with status {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        
        except requests.exceptions.Timeout:
            print(f"  ✗ Request timed out after 60 seconds")
            return False
        
        except Exception as e:
            print(f"  ✗ Error sending batch: {e}")
            return False
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 INGESTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total messages processed: {len(chat_logs)}")
    print(f"✓ Successfully processed: {total_success}")
    print(f"✗ Failed: {total_failed}")
    
    if all_errors:
        print(f"\n⚠ Total errors: {len(all_errors)}")
        print(f"First few errors:")
        for error in all_errors[:5]:
            print(f"  - {error}")
    
    return total_failed == 0


def main():
    """Main execution function"""
    print("="*60)
    print("Knowledge-Weaver Data Ingestion Script")
    print("="*60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Sample data: {SAMPLE_DATA_FILE}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    # Step 1: Check backend health
    print("\n[1/4] Checking backend health...")
    if not check_backend_health():
        print("\n❌ Ingestion aborted: Backend is not available")
        sys.exit(1)
    
    # Step 2: Load sample data
    print("\n[2/4] Loading sample data...")
    raw_logs = load_sample_data(SAMPLE_DATA_FILE)
    
    # Step 3: Format data
    print("\n[3/4] Formatting chat logs...")
    formatted_logs = format_chat_logs(raw_logs)
    print(f"✓ Formatted {len(formatted_logs)} messages")
    
    # Step 4: Ingest data
    print("\n[4/4] Ingesting data to backend...")
    success = ingest_chat_logs(formatted_logs)
    
    # Final result
    print("\n" + "="*60)
    if success:
        print("✅ INGESTION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nYou can now:")
        print("  1. Query the knowledge base via the API")
        print("  2. Use the Chrome Extension to search")
        print("  3. View metrics in the Leadership Dashboard")
        sys.exit(0)
    else:
        print("❌ INGESTION FAILED")
        print("="*60)
        print("\nPlease check the errors above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
