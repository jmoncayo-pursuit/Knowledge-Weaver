
import chromadb
import uuid
from datetime import datetime, timedelta
import os
import sys

def reset_demo_entries():
    # Setup Chroma
    current_dir = os.getcwd()
    persist_directory = os.path.join(current_dir, "backend_api", "chroma_db")
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(name="knowledge_base")
    
    # 1. Inject "Marriage QLE" Entry for Clip 3
    # Timestamp: Tomorrow (to ensure top)
    future_time_1 = (datetime.now() + timedelta(days=1)).isoformat()
    content_qle = """
[10:15:00] Agent_Sarah: I have an employee (ID: 88421) on the line. They are trying to add their spouse for medical coverage.
[10:15:45] Lead_Mark: Okay, what is the Qualifying Life Event?
[10:16:10] Agent_Sarah: Marriage. But the date of marriage was 45 days ago. They just returned from honeymoon.
[10:17:00] Lead_Mark: That is unfortunate. The QLE policy is strict. Documentation must be submitted within 31 days of the event.
[10:17:30] Agent_Sarah: No exceptions? They are only 2 weeks late.
[10:18:00] Lead_Mark: No exceptions. If we allow one, we risk compliance audit failures. Their request is denied. They must wait for Open Enrollment.
[10:18:45] Agent_Sarah: Understood. I will inform them.
    """.strip()
    
    summary_qle = "Review: Employee denied marriage QLE documentation due to 31-day deadline miss."
    
    metadata_qle = {
        "url": f"demo_clip3_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": future_time_1,
        "type": "chat_log",
        "has_screenshot": False,
        "category": "Uncategorized", 
        "tags": "", 
        "summary": summary_qle,
        "verification_status": "draft",
        "is_deleted": False
    }
    
    # 2. Inject "Test Capture" Entry for Clip 4
    # Timestamp: Tomorrow + 1 hour (to be second or near top)
    future_time_2 = (datetime.now() + timedelta(days=1, hours=1)).isoformat()
    content_test = """
[09:00:00] Agent_Bob: Just testing the new capture system.
[09:00:05] Lead_Alice: confirmed.
    """.strip()
    
    summary_test = "Test Capture for Deletion Demo"
    
    metadata_test = {
        "url": f"demo_clip4_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": future_time_2,
        "type": "chat_log",
        "has_screenshot": False,
        "category": "System Test", 
        "tags": "test,ignore",
        "summary": summary_test,
        "verification_status": "draft",
        "is_deleted": False
    }

    # Dummy embedding
    embedding = [0.0] * 768

    print(f"Injecting Clip 3 Entry: {summary_qle}")
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[content_qle],
        embeddings=[embedding],
        metadatas=[metadata_qle]
    )

    print(f"Injecting Clip 4 Entry: {summary_test}")
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[content_test],
        embeddings=[embedding],
        metadatas=[metadata_test]
    )
    
    print("Success! Demo entries injected.")

if __name__ == "__main__":
    reset_demo_entries()
