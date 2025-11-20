"""
Pydantic data models for Knowledge-Weaver Backend API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Model for chat messages from platforms like MS Teams"""
    id: str
    timestamp: datetime
    sender: str
    content: str
    platform: Optional[str] = None
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeEntry(BaseModel):
    """Model for extracted knowledge entries"""
    id: str
    content: str
    entry_type: str = Field(description="Type: 'qa', 'policy', or 'decision'")
    source_messages: List[str] = Field(description="List of source message IDs")
    timestamp: datetime
    participants: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceMetadata(BaseModel):
    """Metadata about the source of knowledge"""
    timestamp: datetime
    participants: List[str]
    chat_id: str
    platform: str


class KnowledgeMatch(BaseModel):
    """Model for a single knowledge match result"""
    knowledge_id: str
    content: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    source: SourceMetadata


class QueryResult(BaseModel):
    """Model for query results from knowledge base"""
    query_id: str
    query_text: str
    timestamp: datetime
    results: List[KnowledgeMatch]
    processing_time_ms: int


class UnansweredQuestion(BaseModel):
    """Model for tracking unanswered agent questions"""
    question_id: str
    question_text: str
    agent: str
    timestamp: datetime
    age_hours: float
    thread_id: str


# Request/Response Schemas for API Endpoints

class ProcessChatLogsRequest(BaseModel):
    """Request schema for processing chat logs"""
    chat_logs: List[ChatMessage] = Field(max_length=100, description="Max 100 messages per batch")


class ProcessingResult(BaseModel):
    """Response schema for chat log processing"""
    success_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    processed_ids: List[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Request schema for knowledge base queries"""
    query: str = Field(min_length=1, description="Natural language query")


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    vector_db: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IngestRequest(BaseModel):
    """Request model for manual knowledge ingestion"""
    text: str = Field(..., description="The text content to ingest")
    url: str = Field(..., description="Source URL of the content")
    screenshot: Optional[str] = Field(None, description="Base64 encoded screenshot")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the content")
    category: Optional[str] = Field(None, description="Category of the content")
    tags: Optional[List[str]] = Field(None, description="Tags for the content")
    summary: Optional[str] = Field(None, description="Summary of the content")

class IngestResponse(BaseModel):
    """Response model for ingestion"""
    status: str
    message: str
    id: Optional[str] = None

class AnalyzeResponse(BaseModel):
    """Response model for content analysis"""
    category: str
    tags: List[str]
    summary: str
