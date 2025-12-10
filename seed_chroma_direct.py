import chromadb
from chromadb.config import Settings
import datetime

def seed_chroma():
    persist_dir = "backend_api/chroma_db"
    print(f"Connecting to ChromaDB at {persist_dir}...")
    
    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(
        anonymized_telemetry=False
    ))
    
    collection = client.get_or_create_collection("knowledge_base")
    print(f"Collection 'knowledge_base' has {collection.count()} entries.")
    
    # Entry Data
    entry_id = "demo_scenario1_seed"
    content = "Employee requesting to add spouse to insurance outside of open enrollment period. Denied due to strict policy on QLE timing."
    metadata = {
        "source": "seed_script",
        "category": "Uncategorized", 
        "tags": "marriage, insurance",
        "timestamp": datetime.datetime.now().isoformat(),
        "summary": "Employee spouse addition request (Denied)",
        "verification_status": "unverified",
        "type": "email"
    }
    dummy_embedding = [0.1] * 768

    print(f"Upserting entry '{entry_id}'...")
    collection.upsert(
        ids=[entry_id],
        documents=[content],
        metadatas=[metadata],
        embeddings=[dummy_embedding]
    )
    
    print("Success! Entry injected.")
    print(f"New count: {collection.count()}")

if __name__ == "__main__":
    seed_chroma()
