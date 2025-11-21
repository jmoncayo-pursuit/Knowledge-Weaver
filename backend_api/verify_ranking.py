import sys
import os
import uuid
from services.vector_db import VectorDatabase
from services.gemini_client import GeminiClient

# Mock Gemini Client to avoid API calls and ensure consistent embeddings
class MockGeminiClient:
    def generate_embedding(self, text):
        # Return a dummy embedding of correct dimension (768)
        return [0.1] * 768

def verify_ranking():
    print("Verifying Source of Truth ranking...")
    
    # Initialize DB
    vector_db = VectorDatabase()
    vector_db.initialize()
    
    # Initialize Mock Gemini
    gemini_client = MockGeminiClient()
    
    # Create test entries
    # Both have similar text/embedding for this test
    query = "What is the policy on X?"
    
    # 1. Unverified entry (but maybe slightly better match textually if we were using real embeddings, 
    # here we use identical embeddings so raw similarity is equal, 
    # but we want to ensure verified wins ties or boosts)
    # To strictly test the boost, we should ideally have the unverified one have a *higher* similarity 
    # if possible, but with mock embeddings they are equal. 
    # The sort is stable for equal keys in Python, but we rely on the boost.
    
    id_unverified = str(uuid.uuid4())
    text_unverified = "I think the policy on X is Y."
    embedding_unverified = gemini_client.generate_embedding(text_unverified)
    metadata_unverified = {
        "verification_status": "unverified",
        "type": "chat_log",
        "timestamp": "2025-01-01T12:00:00"
    }
    
    id_verified = str(uuid.uuid4())
    text_verified = "Official Policy: The policy on X is Y."
    embedding_verified = gemini_client.generate_embedding(text_verified)
    metadata_verified = {
        "verification_status": "verified_human",
        "type": "manual_ingestion",
        "timestamp": "2025-01-01T10:00:00" # Older timestamp to ensure it's not winning by recency (if that were a factor)
    }
    
    print("Ingesting test entries...")
    vector_db.add_knowledge(
        ids=[id_unverified, id_verified],
        documents=[text_unverified, text_verified],
        embeddings=[embedding_unverified, embedding_verified],
        metadatas=[metadata_unverified, metadata_verified]
    )
    
    print("Searching...")
    # Search with same embedding
    query_embedding = gemini_client.generate_embedding(query)
    results = vector_db.search(query_embedding, top_k=10)
    
    print(f"Found {len(results)} results.")
    
    found_verified = False
    found_unverified = False
    verified_rank = -1
    unverified_rank = -1
    
    for i, result in enumerate(results):
        status = result['metadata'].get('verification_status', 'unknown')
        print(f"Rank {i+1}: {result['document'][:50]}... [Status: {status}]")
        
        if result['id'] == id_verified:
            found_verified = True
            verified_rank = i
        elif result['id'] == id_unverified:
            found_unverified = True
            unverified_rank = i
            
    if found_verified and found_unverified:
        if verified_rank < unverified_rank:
            print("\n✅ SUCCESS: Verified entry is ranked higher than unverified entry.")
            # Cleanup (optional, but good for local dev)
            # vector_db.collection.delete(ids=[id_verified, id_unverified])
            sys.exit(0)
        else:
            print("\n❌ FAILURE: Verified entry is NOT ranked higher.")
            sys.exit(1)
    else:
        print("\n❌ FAILURE: Could not find both test entries in results.")
        sys.exit(1)

if __name__ == "__main__":
    verify_ranking()
