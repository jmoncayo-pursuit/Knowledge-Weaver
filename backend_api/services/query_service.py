"""
Query Service for Knowledge-Weaver
Handles natural language queries and retrieves relevant knowledge from Vector Database
"""
import logging
import uuid
import time
import json
import os
from typing import List, Dict, Any
from datetime import datetime

from models.schemas import QueryResult, KnowledgeMatch, SourceMetadata
from services.gemini_client import GeminiClient
from services.vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class QueryService:
    """Handles knowledge base queries and retrieval"""
    
    def __init__(self, vector_db: VectorDatabase, gemini_client: GeminiClient):
        """
        Initialize QueryService with required services
        
        Args:
            vector_db: VectorDatabase instance for searching
            gemini_client: GeminiClient instance for generating query embeddings
        """
        self.vector_db = vector_db
        self.gemini_client = gemini_client
        # Use absolute path to ensure file is always in backend_api directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.query_log_file = os.path.join(backend_dir, 'query_log.jsonl')
        logger.info(f"QueryService initialized, query log file: {self.query_log_file}")
    
    def query_knowledge_base(self, query: str) -> QueryResult:
        """
        Query the knowledge base with natural language
        
        Args:
            query: Natural language query string
        
        Returns:
            QueryResult with matching knowledge entries and metadata
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        query_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Processing query {query_id}: {query[:100]}...")
        
        try:
            # Step 1: Generate query embedding
            query_embedding = self._generate_query_embedding(query)
            
            # Step 2: Search similar knowledge in Vector Database
            matches = self._search_similar_knowledge(query_embedding)
            
            # Step 3: Convert matches to KnowledgeMatch objects
            knowledge_matches = self._format_matches(matches)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create QueryResult
            result = QueryResult(
                query_id=query_id,
                query_text=query,
                timestamp=datetime.utcnow(),
                results=knowledge_matches,
                processing_time_ms=processing_time_ms
            )
            
            # Log query for analytics
            self._log_query(query_id, query, len(knowledge_matches), processing_time_ms)
            
            logger.info(f"Query {query_id} completed: {len(knowledge_matches)} matches in {processing_time_ms}ms")
            
            return result
        
        except Exception as e:
            logger.error(f"Query {query_id} failed: {e}", exc_info=True)
            
            # Return empty result on error
            processing_time_ms = int((time.time() - start_time) * 1000)
            return QueryResult(
                query_id=query_id,
                query_text=query,
                timestamp=datetime.utcnow(),
                results=[],
                processing_time_ms=processing_time_ms
            )
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for the query using Gemini API
        
        Args:
            query: Query text
        
        Returns:
            Query embedding vector
        """
        try:
            embedding = self.gemini_client.generate_query_embedding(query)
            logger.debug(f"Generated query embedding of dimension {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
    
    def _search_similar_knowledge(
        self,
        embedding: List[float],
        threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Search for similar knowledge entries using vector similarity
        
        Args:
            embedding: Query embedding vector
            threshold: Minimum similarity score threshold (default: 0.1)
        
        Returns:
            List of matching knowledge entries with metadata
        """
        try:
            matches = self.vector_db.search(
                query_embedding=embedding,
                top_k=3,
                threshold=threshold
            )
            
            logger.debug(f"Found {len(matches)} matches above threshold {threshold}")
            return matches
        
        except Exception as e:
            logger.error(f"Vector database search failed: {e}")
            raise
    
    def _format_matches(self, matches: List[Dict[str, Any]]) -> List[KnowledgeMatch]:
        """
        Format raw matches into KnowledgeMatch objects
        
        Args:
            matches: Raw matches from vector database
        
        Returns:
            List of KnowledgeMatch objects
        """
        knowledge_matches = []
        
        for match in matches:
            try:
                # Extract metadata
                metadata = match.get('metadata', {})
                
                # Parse timestamp
                timestamp_str = metadata.get('timestamp', datetime.utcnow().isoformat())
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except (ValueError, TypeError):
                    timestamp = datetime.utcnow()
                
                # Parse participants
                participants_str = metadata.get('participants', '')
                participants = participants_str.split(',') if participants_str else []
                
                # Create SourceMetadata
                source = SourceMetadata(
                    timestamp=timestamp,
                    participants=participants,
                    chat_id=metadata.get('source_message_ids', match.get('id', '')),
                    platform=metadata.get('platform', 'teams')
                )
                
                # Create KnowledgeMatch
                knowledge_match = KnowledgeMatch(
                    knowledge_id=match.get('id', ''),
                    content=match.get('document', ''),
                    similarity_score=match.get('similarity_score', 0.0),
                    source=source
                )
                
                knowledge_matches.append(knowledge_match)
            
            except Exception as e:
                logger.warning(f"Failed to format match: {e}")
                continue
        
        return knowledge_matches
    
    def _log_query(
        self,
        query_id: str,
        query_text: str,
        result_count: int,
        processing_time_ms: int
    ) -> None:
        """
        Log query for analytics and trending topics analysis
        Appends query as JSON line to query_log.jsonl file
        
        Args:
            query_id: Unique query identifier
            query_text: The query text
            result_count: Number of results returned
            processing_time_ms: Processing time in milliseconds
        """
        log_entry = {
            'query_id': query_id,
            'query_text': query_text,
            'result_count': result_count,
            'processing_time_ms': processing_time_ms,
            'timestamp': datetime.utcnow().isoformat(),
            'has_results': result_count > 0
        }
        
        # Append query as JSON line to file
        try:
            with open(self.query_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
            logger.debug(f"Logged query {query_id} to {self.query_log_file}")
        except Exception as e:
            logger.error(f"Failed to write query log: {e}", exc_info=True)
    
    def get_query_logs(
        self,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve query logs for analytics
        Reads from query_log.jsonl file
        
        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of logs to return
        
        Returns:
            List of query log entries
        """
        logs = []
        
        # Read logs from JSONL file
        if os.path.exists(self.query_log_file):
            try:
                with open(self.query_log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                log_entry = json.loads(line)
                                logs.append(log_entry)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse log line: {e}")
                                continue
            except Exception as e:
                logger.error(f"Failed to read query log file: {e}", exc_info=True)
        
        # Apply date filters if provided
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) >= start_dt]
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) <= end_dt]
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")
        
        # Apply limit
        logs = logs[-limit:] if limit else logs
        
        return logs
