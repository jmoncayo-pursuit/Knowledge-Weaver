"""
API Routes for Knowledge-Weaver Backend
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas import (
    ProcessChatLogsRequest,
    ProcessingResult,
    QueryRequest,
    QueryResult,
    HealthResponse
)
from auth import verify_api_key
from services.vector_db import VectorDatabase
from services.gemini_client import GeminiClient
from services.chat_processor import ChatLogProcessor
from services.query_service import QueryService

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["api"])

# Global service instances (will be initialized in main.py)
vector_db: VectorDatabase = None
gemini_client: GeminiClient = None
chat_processor: ChatLogProcessor = None
query_service: QueryService = None


def get_services():
    """Dependency to ensure services are initialized"""
    if not all([vector_db, gemini_client, chat_processor, query_service]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services not initialized"
        )
    return {
        "vector_db": vector_db,
        "gemini_client": gemini_client,
        "chat_processor": chat_processor,
        "query_service": query_service
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    No authentication required
    """
    try:
        # Check vector database status
        if vector_db and vector_db.collection:
            db_status = "connected"
            stats = vector_db.get_collection_stats()
            logger.info(f"Health check: {stats}")
        else:
            db_status = "not_initialized"
        
        return HealthResponse(
            status="healthy",
            vector_db=db_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            vector_db="error"
        )


@router.post("/chat-logs/process", response_model=ProcessingResult)
async def process_chat_logs(
    request: ProcessChatLogsRequest,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Process chat logs and extract knowledge
    Requires API key authentication
    
    Args:
        request: ProcessChatLogsRequest with chat_logs array
        api_key: Validated API key from header
        services: Injected services
    
    Returns:
        ProcessingResult with success/failure counts
    """
    logger.info(f"Processing {len(request.chat_logs)} chat messages")
    
    try:
        # Validate batch size
        if len(request.chat_logs) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 messages per batch"
            )
        
        # Process chat logs
        result = services["chat_processor"].process_chat_logs(request.chat_logs)
        
        return ProcessingResult(
            success_count=result["success_count"],
            failed_count=result["failed_count"],
            errors=result["errors"],
            processed_ids=result["processed_ids"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process chat logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat logs: {str(e)}"
        )


@router.post("/knowledge/query", response_model=QueryResult)
async def query_knowledge(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Query the knowledge base with natural language
    Requires API key authentication
    
    Args:
        request: QueryRequest with query string
        api_key: Validated API key from header
        services: Injected services
    
    Returns:
        QueryResult with matching knowledge entries
    """
    logger.info(f"Querying knowledge base: {request.query[:100]}...")
    
    try:
        # Query knowledge base
        result = services["query_service"].query_knowledge_base(request.query)
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/metrics/queries")
async def get_query_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Retrieve query logs for analytics
    Requires API key authentication
    
    Args:
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        limit: Maximum number of logs to return
        api_key: Validated API key from header
        services: Injected services
    
    Returns:
        Array of query log entries
    """
    logger.info(f"Fetching query metrics (limit: {limit})")
    
    try:
        logs = services["query_service"].get_query_logs(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {"logs": logs, "count": len(logs)}
    
    except Exception as e:
        logger.error(f"Failed to fetch query metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )


@router.get("/metrics/unanswered")
async def get_unanswered_questions(
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Get unanswered questions from chat logs
    Requires API key authentication
    
    Note: This is a placeholder endpoint. Full implementation requires
    additional logic to track unanswered questions from chat logs.
    
    Args:
        api_key: Validated API key from header
        services: Injected services
    
    Returns:
        Array of unanswered question entries
    """
    logger.info("Fetching unanswered questions")
    
    # Placeholder implementation
    # In a full implementation, this would query a separate tracking system
    return {
        "unanswered_questions": [],
        "count": 0,
        "message": "Unanswered questions tracking not yet implemented"
    }
