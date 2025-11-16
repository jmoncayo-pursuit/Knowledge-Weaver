"""
Chat Log Processor for Knowledge-Weaver
Analyzes historical chat logs and extracts knowledge for indexing
"""
import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime

from models.schemas import ChatMessage, KnowledgeEntry
from services.gemini_client import GeminiClient
from services.vector_db import VectorDatabase
from services.anonymizer import AnonymizerService

logger = logging.getLogger(__name__)


class ChatLogProcessor:
    """Processes chat logs to extract and index knowledge"""
    
    def __init__(self, gemini_client: GeminiClient, vector_db: VectorDatabase):
        """
        Initialize ChatLogProcessor with required services
        
        Args:
            gemini_client: GeminiClient instance for AI operations
            vector_db: VectorDatabase instance for storage
        """
        self.gemini_client = gemini_client
        self.vector_db = vector_db
        self.anonymizer = AnonymizerService()
        logger.info("ChatLogProcessor initialized with HIPAA-compliant anonymization")
    
    def process_chat_logs(self, chat_logs: List[ChatMessage]) -> Dict[str, Any]:
        """
        Process chat logs end-to-end: extract knowledge, generate embeddings, and store
        
        Args:
            chat_logs: List of ChatMessage objects to process
        
        Returns:
            Dictionary with processing results including success/failure counts
        """
        if not chat_logs:
            logger.warning("No chat logs provided for processing")
            return {
                "success_count": 0,
                "failed_count": 0,
                "errors": [],
                "processed_ids": []
            }
        
        logger.info(f"Starting processing of {len(chat_logs)} chat messages")
        
        errors = []
        processed_ids = []
        
        try:
            # Step 0: Anonymize chat logs for HIPAA compliance
            logger.info("Step 0: Anonymizing chat logs for HIPAA compliance")
            anonymized_logs = self._anonymize_chat_logs(chat_logs)
            
            # Step 1: Extract knowledge from anonymized chat messages using Gemini
            logger.info("Step 1: Extracting knowledge from anonymized chat messages")
            knowledge_dicts = self.gemini_client.process_messages_in_batches(anonymized_logs)
            
            if not knowledge_dicts:
                logger.warning("No knowledge extracted from chat logs")
                return {
                    "success_count": 0,
                    "failed_count": len(chat_logs),
                    "errors": ["No knowledge could be extracted from the provided messages"],
                    "processed_ids": []
                }
            
            logger.info(f"Extracted {len(knowledge_dicts)} knowledge entries")
            
            # Step 2: Generate embeddings for each knowledge entry
            logger.info("Step 2: Generating embeddings for knowledge entries")
            embeddings_data = self._create_embeddings(knowledge_dicts)
            
            if not embeddings_data:
                logger.error("Failed to generate embeddings")
                return {
                    "success_count": 0,
                    "failed_count": len(chat_logs),
                    "errors": ["Failed to generate embeddings for extracted knowledge"],
                    "processed_ids": []
                }
            
            # Step 3: Store in Vector Database
            logger.info("Step 3: Storing knowledge entries in Vector Database")
            self._store_knowledge(embeddings_data)
            
            processed_ids = embeddings_data["ids"]
            success_count = len(processed_ids)
            
            logger.info(f"Successfully processed {success_count} knowledge entries")
            
            return {
                "success_count": success_count,
                "failed_count": 0,
                "errors": errors,
                "processed_ids": processed_ids
            }
        
        except Exception as e:
            error_msg = f"Failed to process chat logs: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            return {
                "success_count": len(processed_ids),
                "failed_count": len(chat_logs) - len(processed_ids),
                "errors": errors,
                "processed_ids": processed_ids
            }
    
    def _anonymize_chat_logs(self, chat_logs: List[ChatMessage]) -> List[ChatMessage]:
        """
        Anonymize sensitive data in chat logs before processing
        HIPAA compliance requirement
        
        Args:
            chat_logs: List of ChatMessage objects with potentially sensitive data
        
        Returns:
            List of ChatMessage objects with anonymized content
        """
        anonymized_logs = []
        
        for log in chat_logs:
            # Create a copy of the message with anonymized content
            anonymized_log = ChatMessage(
                id=log.id,
                timestamp=log.timestamp,
                sender=log.sender,
                content=self.anonymizer.anonymize_text(log.content),
                platform=log.platform,
                thread_id=log.thread_id,
                metadata=log.metadata
            )
            anonymized_logs.append(anonymized_log)
        
        logger.info(f"Anonymized {len(chat_logs)} chat messages for HIPAA compliance")
        return anonymized_logs
    
    def _create_embeddings(self, knowledge_dicts: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Generate embeddings for extracted knowledge entries
        
        Args:
            knowledge_dicts: List of knowledge entry dictionaries
        
        Returns:
            Dictionary with ids, documents, embeddings, and metadatas lists
        """
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for knowledge_dict in knowledge_dicts:
            try:
                # Generate unique ID for this knowledge entry
                knowledge_id = str(uuid.uuid4())
                
                # Extract content
                content = knowledge_dict.get("content", "")
                if not content:
                    logger.warning("Skipping knowledge entry with empty content")
                    continue
                
                # Generate embedding
                embedding = self.gemini_client.generate_embedding(content)
                
                if not embedding:
                    logger.warning(f"Failed to generate embedding for knowledge entry {knowledge_id}")
                    continue
                
                # Prepare metadata
                metadata = {
                    "entry_type": knowledge_dict.get("entry_type", "qa"),
                    "confidence_score": knowledge_dict.get("confidence_score", 0.7),
                    "timestamp": datetime.utcnow().isoformat(),
                    "participants": ",".join(knowledge_dict.get("participants", [])),
                    "source_message_ids": ",".join(knowledge_dict.get("source_message_ids", []))
                }
                
                ids.append(knowledge_id)
                documents.append(content)
                embeddings.append(embedding)
                metadatas.append(metadata)
            
            except Exception as e:
                logger.error(f"Failed to process knowledge entry: {e}")
                continue
        
        logger.info(f"Generated {len(embeddings)} embeddings from {len(knowledge_dicts)} knowledge entries")
        
        return {
            "ids": ids,
            "documents": documents,
            "embeddings": embeddings,
            "metadatas": metadatas
        }
    
    def _store_knowledge(self, embeddings_data: Dict[str, List]) -> None:
        """
        Store knowledge entries with embeddings in Vector Database
        
        Args:
            embeddings_data: Dictionary containing ids, documents, embeddings, and metadatas
        """
        if not embeddings_data["ids"]:
            logger.warning("No embeddings data to store")
            return
        
        try:
            self.vector_db.add_knowledge(
                ids=embeddings_data["ids"],
                documents=embeddings_data["documents"],
                embeddings=embeddings_data["embeddings"],
                metadatas=embeddings_data["metadatas"]
            )
            logger.info(f"Stored {len(embeddings_data['ids'])} knowledge entries in Vector Database")
        
        except Exception as e:
            logger.error(f"Failed to store knowledge in Vector Database: {e}")
            raise
