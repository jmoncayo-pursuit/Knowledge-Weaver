import chromadb
from chromadb.config import Settings
import os
import json

def verify_persistence():
    print("Verifying persistence of #DashboardReady tag...")
    
    # Connect to ChromaDB
    persist_dir = "./chroma_db"
    client = chromadb.PersistentClient(path=persist_dir)
    
    try:
        collection = client.get_collection("knowledge_base")
        
        # Query by URL which we know from the mock
        results = collection.get(
            where={"url": "http://localhost:8000/demo-context"}
        )
        
        found = False
        if results and results['ids']:
            for i, metadata in enumerate(results['metadatas']):
                tags = metadata.get('tags', '')
                print(f"Checking entry {results['ids'][i]} with tags: {tags}")
                
                if "#DashboardReady" in tags:
                    print(f"\nSUCCESS: Found entry with #DashboardReady tag.")
                    print(f"Full Metadata: {json.dumps(metadata, indent=2)}")
                    found = True
                    break
        
        if not found:
            print("\nFAILURE: No entry found with #DashboardReady tag.")
            
            # Debug: List all entries
            all_results = collection.get()
            print(f"\nTotal entries in DB: {len(all_results['ids'])}")
            
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    verify_persistence()
