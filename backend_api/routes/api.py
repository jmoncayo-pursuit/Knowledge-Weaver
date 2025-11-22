"""
API Routes for Knowledge-Weaver Backend
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from models.schemas import (
    ProcessChatLogsRequest,
    ProcessingResult,
    QueryRequest,
    QueryResult,
    IngestRequest,
    IngestRequest,
    IngestResponse,
    UpdateKnowledgeRequest,
    UpdateKnowledgeRequest,
    AnalyzeResponse,
    DashboardMetricsResponse,
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
        result = services["query_service"].query_knowledge_base(
            query=request.query,
            verified_only=request.verified_only
        )
        
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


@router.get("/knowledge/recent")
async def get_recent_knowledge(
    limit: int = 10,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Get recent knowledge entries
    Requires API key authentication
    """
    logger.info(f"Fetching recent knowledge (limit: {limit})")
    
    try:
        entries = services["vector_db"].get_recent_entries(limit=limit)
        return entries
    
    except Exception as e:
        logger.error(f"Failed to fetch recent knowledge: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent knowledge: {str(e)}"
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



@router.get("/metrics/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Get aggregated metrics for the leadership dashboard
    Requires API key authentication
    """
    logger.info("Fetching dashboard metrics")
    
    try:
        # 1. Get Total Knowledge Count
        collection_stats = services["vector_db"].get_collection_stats()
        total_knowledge = collection_stats.get("count", 0) if collection_stats.get("status") == "initialized" else 0
        
        # 2. Get Verified Count
        verified_count = services["vector_db"].get_verified_count()
        
        # 3. Calculate Verified Ratio
        verified_ratio = (verified_count / total_knowledge * 100) if total_knowledge > 0 else 0.0
        
        # 4. Get Query Stats (Volume & Gaps)
        query_stats = services["query_service"].get_query_stats(days=7)
        
        # 5. Get Recent Knowledge Gaps
        recent_gaps = services["query_service"].get_knowledge_gaps(limit=5)
        
        return DashboardMetricsResponse(
            total_knowledge=total_knowledge,
            verified_count=verified_count,
            verified_ratio=round(verified_ratio, 1),
            query_volume_7d=query_stats["total_volume"],
            knowledge_gaps_7d=query_stats["knowledge_gaps"],
            recent_gaps=recent_gaps
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch dashboard metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard metrics: {str(e)}"
        )




@router.post("/ingest", response_model=IngestResponse)
async def ingest_knowledge(
    request: IngestRequest,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Manually ingest knowledge into the vector database
    """
    try:
        logger.info(f"Received manual ingestion request for URL: {request.url}")
        
        # Generate unique ID
        import uuid
        entry_id = str(uuid.uuid4())
        
        # Generate embedding
        embedding = services["gemini_client"].generate_embedding(request.text)
        
        # Prepare metadata
        metadata = {
            "url": request.url,
            "timestamp": request.timestamp.isoformat(),
            "type": "manual_ingestion",
            "has_screenshot": bool(request.screenshot),
            "category": request.category or "Uncategorized",
            "tags": ",".join(request.tags) if request.tags else "",
            "summary": request.summary or "",
            "verification_status": "verified_human"
        }
        
        # Add to vector database
        services["vector_db"].add_knowledge(
            ids=[entry_id],
            documents=[request.text],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        
        return IngestResponse(
            status="success",
            message="Knowledge ingested successfully",
            id=entry_id
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Ingestion failed: {str(e)}"
            }
        )

@router.delete("/knowledge/{entry_id}")
async def delete_knowledge_entry(
    entry_id: str,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Delete a knowledge entry
    Requires API key authentication
    """
    logger.info(f"Deleting knowledge entry: {entry_id}")
    
    try:
        success = services["vector_db"].delete_entry(entry_id)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "success", "message": f"Entry {entry_id} deleted"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete entry"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )

@router.patch("/knowledge/{entry_id}")
async def update_knowledge_entry(
    entry_id: str,
    request: UpdateKnowledgeRequest,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Update a knowledge entry
    Automatically sets verification_status to 'verified_human'
    Requires API key authentication
    """
    logger.info(f"Updating knowledge entry: {entry_id}")
    
    try:
        # Prepare updates
        updates = {}
        if request.category is not None:
            updates["category"] = request.category
        if request.tags is not None:
            updates["tags"] = ",".join(request.tags)
        if request.summary is not None:
            updates["summary"] = request.summary
            
        # Force verification status update (Active Learning)
        updates["verification_status"] = "verified_human"
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )
            
        success = services["vector_db"].update_entry(entry_id, updates)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "success", "message": f"Entry {entry_id} updated"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry not found or update failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(
    request: IngestRequest,
    x_api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Analyze content to extract category, tags, and summary
    """
    try:
        logger.info(f"Analyzing content for URL: {request.url}")
        
        # Step 1: Generate embedding for the input text
        embedding = services["gemini_client"].generate_embedding(request.text)
        
        # Step 2: Find similar verified entries
        similar_verified = services["vector_db"].find_similar_verified(embedding)
        
        # Step 3: Format context examples
        context_examples = ""
        if similar_verified:
            logger.info(f"Found {len(similar_verified)} similar verified entries for context")
            examples_list = []
            for i, match in enumerate(similar_verified):
                content = match['document']
                category = match['metadata'].get('category', 'Unknown')
                tags = match['metadata'].get('tags', '')
                examples_list.append(f"Example {i+3}:\nInput: \"{content}\"\nOutput Category: \"{category}\"\nTags: {tags}")
            
            context_examples = "\n\n".join(examples_list)
        
        # Step 4: Analyze with context
        analysis = services["gemini_client"].analyze_content(
            request.text, 
            context_examples=context_examples
        )
        
        return AnalyzeResponse(
            category=analysis["category"],
            tags=analysis["tags"],
            summary=analysis["summary"]
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }
        )
