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
    AnalyzeResponse,
    DashboardMetricsResponse,
    HealthResponse,
    DashboardMetricsResponse,
    HealthResponse,
    BarrierLogRequest,
    LearningEvent
)
import json
import os
from datetime import datetime
from auth import verify_api_key
from services.vector_db import VectorDatabase
from services.gemini_client import GeminiClient
from services.chat_processor import ChatLogProcessor
from services.query_service import QueryService
from services.anonymizer import AnonymizerService

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["api"])

# Global service instances (will be initialized in main.py)
vector_db: VectorDatabase = None
gemini_client: GeminiClient = None
chat_processor: ChatLogProcessor = None
query_service: QueryService = None
anonymizer_service: AnonymizerService = None


def get_services():
    """Dependency to ensure services are initialized"""
    # Initialize anonymizer if not already done (it's stateless/lightweight)
    global anonymizer_service
    if not anonymizer_service:
        anonymizer_service = AnonymizerService()

    if not all([vector_db, gemini_client, chat_processor, query_service]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services not initialized"
        )
    return {
        "vector_db": vector_db,
        "gemini_client": gemini_client,
        "chat_processor": chat_processor,
        "query_service": query_service,
        "anonymizer": anonymizer_service
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
    deleted_only: bool = False,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Get recent knowledge entries
    Requires API key authentication
    
    Args:
        limit: Maximum number of entries to return
        deleted_only: If True, return only deleted items (for Recycle Bin)
    """
    logger.info(f"Fetching recent knowledge (limit: {limit}, deleted_only: {deleted_only})")
    
    try:
        entries = services["vector_db"].get_recent_entries(limit=limit, deleted_only=deleted_only)
        return entries
    
    except Exception as e:
        logger.error(f"Failed to fetch recent knowledge: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent knowledge: {str(e)}"
        )



@router.get("/knowledge/trending")
async def get_trending_topics(
    limit: int = 5,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Get trending topics/tags from recent knowledge entries
    Requires API key authentication
    """
    logger.info(f"Fetching trending topics (limit: {limit})")
    
    try:
        # Fetch recent entries to analyze tags
        entries = services["vector_db"].get_recent_entries(limit=50)
        
        tag_counts = {}
        for entry in entries:
            # Handle tags which might be a list or string
            tags = entry.get('metadata', {}).get('tags', [])
            
            # If tags is a string (e.g. "['tag1', 'tag2']"), we might need to parse it
            # But assuming it's a list or comma-separated string based on ingestion
            if isinstance(tags, str):
                # Split by comma if it's a simple string
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            elif isinstance(tags, list):
                tag_list = tags
            else:
                tag_list = []
                
            for tag in tag_list:
                # Clean up tag
                tag = tag.strip()
                # Skip system tags or empty
                if tag and not tag.startswith('#KnowledgeGap'):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                        
        # Sort by count
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        trending = [tag for tag, count in sorted_tags[:limit]]
        
        # If not enough tags, provide some defaults
        if not trending:
            trending = ["Policy", "HR", "Technical", "Sales", "Procedure"]
            
        return trending
        
    except Exception as e:
        logger.error(f"Failed to fetch trending topics: {e}", exc_info=True)
        # Return defaults on error to keep UI working
        return ["Policy", "HR", "Technical", "Sales", "Procedure"]

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
        
    except Exception as e:
        logger.error(f"Failed to fetch dashboard metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard metrics: {str(e)}"
        )


@router.get("/metrics/learning", response_model=List[LearningEvent])
async def get_learning_history(
    limit: int = 5,
    api_key: str = Depends(verify_api_key)
):
    """
    Get recent learning events (AI vs Human corrections)
    """
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(backend_dir, 'learning_history.jsonl')
        
        events = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                # Read all lines
                lines = f.readlines()
                # Parse last 'limit' lines in reverse order
                for line in reversed(lines):
                    if len(events) >= limit:
                        break
                    try:
                        if line.strip():
                            events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                        
        return events
        
    except Exception as e:
        logger.error(f"Failed to fetch learning history: {e}", exc_info=True)
        return []


@router.get("/metrics/learning_stats")
async def get_learning_stats(
    limit: int = 5,
    api_key: str = Depends(verify_api_key)
):
    """
    Get aggregated learning statistics (Top learned tags)
    """
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(backend_dir, 'learning_history.jsonl')
        
        tag_counts = {}
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        if line.strip():
                            event = json.loads(line)
                            # Count tags in human correction
                            # We only care about what the human TAUGHT the AI
                            human_tags = event.get('human_correction', {}).get('tags', [])
                            ai_tags = event.get('ai_prediction', {}).get('tags', [])
                            
                            # Identify NEW tags (what was learned)
                            learned_tags = [t for t in human_tags if t not in ai_tags]
                            
                            for tag in learned_tags:
                                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                                
                    except json.JSONDecodeError:
                        continue
        
        # Sort by count
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        top_tags = [{"tag": tag, "count": count} for tag, count in sorted_tags[:limit]]
        
        return {
            "top_learned_tags": top_tags,
            "total_corrections": sum(tag_counts.values())
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch learning stats: {e}", exc_info=True)
        return {"top_learned_tags": [], "total_corrections": 0}


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
        if request.ai_prediction:
            logger.info(f"AI Prediction received: {request.ai_prediction}")
        else:
            logger.info("No AI Prediction in request")
        
        # Generate unique ID
        import uuid
        entry_id = str(uuid.uuid4())
        
        # Anonymize text before processing
        anonymized_text = services["anonymizer"].anonymize_text(request.text)
        if anonymized_text != request.text:
            logger.info("PII detected and redacted from input text")

        # Generate embedding
        embedding = services["gemini_client"].generate_embedding(anonymized_text)
        
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
            documents=[anonymized_text],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        

        
        # --- Learning History Tracking ---
        if request.ai_prediction:
            try:
                # Compare AI prediction with final values
                ai_tags = set(request.ai_prediction.get("tags", []))
                human_tags = set(request.tags or [])
                
                ai_category = request.ai_prediction.get("category")
                human_category = request.category
                
                # Check for differences
                tags_changed = ai_tags != human_tags
                category_changed = ai_category != human_category
                
                if tags_changed or category_changed:
                    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    history_file = os.path.join(backend_dir, 'learning_history.jsonl')
                    
                    learning_event = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "summary": request.summary or "No summary",
                        "ai_prediction": {
                            "tags": list(ai_tags),
                            "category": ai_category
                        },
                        "human_correction": {
                            "tags": list(human_tags),
                            "category": human_category
                        }
                    }
                    
                    with open(history_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(learning_event) + '\n')
                        
                    logger.info("Logged learning event: Human corrected AI")
                    
            except Exception as e:
                logger.error(f"Failed to log learning event: {e}")
        # ---------------------------------
        # ---------------------------------
        
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

@router.post("/knowledge/{entry_id}/restore")
async def restore_knowledge_entry(
    entry_id: str,
    api_key: str = Depends(verify_api_key),
    services: dict = Depends(get_services)
):
    """
    Restore a soft-deleted knowledge entry
    Requires API key authentication
    """
    logger.info(f"Restoring knowledge entry: {entry_id}")
    
    try:
        success = services["vector_db"].restore_entry(entry_id)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "success", "message": f"Entry {entry_id} restored"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore entry"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
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
        if request.screenshot is not None:
            updates["screenshot"] = request.screenshot
            updates["has_screenshot"] = True
            
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

@router.post("/log/barrier")
async def log_robot_barrier(
    request: BarrierLogRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Log a robot barrier event (UI element not found/clickable)
    """
    try:
        # Use absolute path for log file
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(backend_dir, 'robot_barriers.jsonl')
        
        log_entry = request.dict()
        log_entry['timestamp'] = log_entry['timestamp'].isoformat()
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
            f.flush()
            os.fsync(f.fileno())
            
        logger.info(f"Logged robot barrier: {request.error} at {request.selector}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": "Barrier logged"}
        )
        
    except Exception as e:
        logger.error(f"Failed to log barrier: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
