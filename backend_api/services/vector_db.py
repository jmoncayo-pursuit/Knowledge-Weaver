"""
Vector Database Manager for Knowledge-Weaver
Manages ChromaDB operations including initialization, indexing, and persistence
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Manages ChromaDB operations for knowledge storage and retrieval"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB client with persistence
        
        Args:
            persist_directory: Directory path for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory, settings=Settings(
            anonymized_telemetry=False
        ))
        self.collection = None
        logger.info(f"VectorDatabase initialized with persist_directory: {persist_directory}")
    
    COLLECTION_NAME = "knowledge_base"

    def initialize(self) -> None:
        """
        Initialize or get the knowledge_base collection
        Creates the collection if it doesn't exist
        """
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Knowledge entries from chat logs"}
            )
            logger.info(f"Collection 'knowledge_base' initialized with {self.collection.count()} entries")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def add_knowledge(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        Add knowledge entries to the vector database
        
        Args:
            ids: List of unique identifiers for knowledge entries
            documents: List of knowledge text content
            embeddings: List of vector embeddings (768-dimensional for Gemini)
            metadatas: List of metadata dicts (timestamp, participants, source_id, etc.)
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")
        
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Added {len(ids)} knowledge entries to vector database")
        except Exception as e:
            logger.error(f"Failed to add knowledge entries: {e}")
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        threshold: float = 0.1,
        verified_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for similar knowledge entries using vector similarity
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results to return (default: 3)
            threshold: Minimum similarity score threshold (default: 0.5)
            verified_only: If True, return only verified content
        
        Returns:
            List of matching knowledge entries with metadata and similarity scores
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")
        
        try:
            # Prepare query arguments
            query_args = {
                "query_embeddings": [query_embedding],
                "n_results": top_k
            }
            
            # Add filter if verified_only is True
            if verified_only:
                query_args["where"] = {"verification_status": "verified_human"}
            
            results = self.collection.query(**query_args)
            
            # Filter results by similarity threshold
            # ChromaDB returns distances, convert to similarity scores (1 - distance)
            matches = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i]
                    similarity_score = 1 - distance  # Convert distance to similarity
                    
                    # Log distances for debugging
                    logger.debug(f"Result {i}: distance={distance}, similarity={similarity_score}")
                    
                    if similarity_score >= threshold:
                        matches.append({
                            'id': results['ids'][0][i],
                            'document': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity_score': similarity_score
                        })
            
            # Re-ranking logic: Boost "verified_human" entries to the top
            # Sort by verification_status (verified first) then by similarity_score (descending)
            matches.sort(
                key=lambda x: (
                    1 if x['metadata'].get('verification_status') == 'verified_human' else 0,
                    x['similarity_score']
                ),
                reverse=True
            )
            
            logger.info(f"Search returned {len(matches)} matches above threshold {threshold} (total results: {len(results['ids'][0]) if results['ids'] else 0})")
            return matches
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def persist(self) -> None:
        """
        Persist the vector database to disk
        ChromaDB with PersistentClient auto-persists, but this can be called explicitly
        """
        try:
            # ChromaDB with Settings persist_directory auto-persists
            # This method is here for explicit persistence if needed
            logger.info("Vector database persisted to disk")
        except Exception as e:
            logger.error(f"Failed to persist database: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Returns:
            Dictionary with collection statistics
        """
        if not self.collection:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "count": self.collection.count(),
            "name": self.collection.name
        }

    def get_recent_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent knowledge entries
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of knowledge entries sorted by timestamp (newest first)
        """
        if not self.collection:
            return []
            
        try:
            # Fetch more to ensure we get recent ones after sorting
            # ChromaDB doesn't support server-side sorting by metadata yet
            # We fetch a larger batch to increase chance of getting recent ones
            results = self.collection.get(
                limit=100,  # Increased from limit * 2
                include=['documents', 'metadatas']
            )
            
            entries = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    entries.append({
                        'id': results['ids'][i],
                        'document': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    })
            
            # Sort by timestamp in metadata (descending)
            entries.sort(
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=True
            )
            
            return entries[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent entries: {e}")
            return []

    def find_similar_verified(
        self,
        query_embedding: List[float],
        n: int = 3,
        threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Find similar verified knowledge entries to serve as few-shot examples
        
        Args:
            query_embedding: Query vector embedding
            n: Number of results to return
            threshold: Minimum similarity score
            
        Returns:
            List of verified knowledge entries
        """
        if not self.collection:
            return []
            
        try:
            # Query specifically for verified entries
            # Note: ChromaDB filtering happens before vector search in some versions,
            # but we'll use the where clause to be safe
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n * 2,  # Fetch more to filter
                where={"verification_status": "verified_human"}
            )
            
            matches = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i]
                    similarity_score = 1 - distance
                    
                    if similarity_score >= threshold:
                        matches.append({
                            'document': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity_score': similarity_score
                        })
            
            # Sort by similarity
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return matches[:n]
            
        except Exception as e:
            logger.error(f"Failed to find similar verified entries: {e}")
            return []

    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a knowledge entry by ID
        
        Args:
            entry_id: ID of the entry to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.collection:
            return False
            
        try:
            self.collection.delete(ids=[entry_id])
            logger.info(f"Deleted entry {entry_id} from vector database")
            return True
        except Exception as e:
            logger.error(f"Failed to delete entry {entry_id}: {e}")
            return False
