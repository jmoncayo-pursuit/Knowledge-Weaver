import chromadb
from chromadb.config import Settings
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def audit_database():
    persist_dir = "./chroma_db"
    collection_name = "knowledge_base"
    
    print(f"Auditing ChromaDB at: {os.path.abspath(persist_dir)}")
    print(f"Target Collection: {collection_name}")
    
    try:
        client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        
        try:
            collection = client.get_collection(name=collection_name)
            count = collection.count()
            print(f"\nTotal Documents: {count}")
            
            if count > 0:
                print("\nLast 5 Documents:")
                # Fetch last 5 docs (limit is not directly supported in peek/get in all versions, using get with limit if possible or just get all and slice)
                # Chroma's get() returns a dict
                data = collection.get(limit=5)
                
                ids = data['ids']
                documents = data['documents']
                metadatas = data['metadatas']
                
                for i in range(len(ids)):
                    print(f"[{i+1}] ID: {ids[i]}")
                    print(f"    Text: {documents[i][:100]}..." if len(documents[i]) > 100 else f"    Text: {documents[i]}")
                    print(f"    Metadata: {metadatas[i]}")
                    print("-" * 40)
            else:
                print("\nCollection is empty.")
                
        except ValueError:
            print(f"\nCollection '{collection_name}' does not exist.")
            
    except Exception as e:
        print(f"\nError accessing database: {e}")

if __name__ == "__main__":
    audit_database()
