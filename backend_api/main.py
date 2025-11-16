"""
Knowledge-Weaver Backend API
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

from services.vector_db import VectorDatabase
from services.gemini_client import GeminiClient
from services.chat_processor import ChatLogProcessor
from services.query_service import QueryService
from routes import api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge-Weaver API",
    description="Backend API for resurrecting knowledge from chat logs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Knowledge-Weaver API starting up...")
    
    try:
        # Initialize Vector Database
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        api.vector_db = VectorDatabase(persist_directory=persist_dir)
        api.vector_db.initialize()
        
        stats = api.vector_db.get_collection_stats()
        logger.info(f"Vector Database initialized: {stats}")
        
        # Initialize Gemini Client
        api.gemini_client = GeminiClient()
        logger.info("Gemini Client initialized")
        
        # Initialize Chat Processor
        api.chat_processor = ChatLogProcessor(
            gemini_client=api.gemini_client,
            vector_db=api.vector_db
        )
        logger.info("Chat Processor initialized")
        
        # Initialize Query Service
        api.query_service = QueryService(
            vector_db=api.vector_db,
            gemini_client=api.gemini_client
        )
        logger.info("Query Service initialized")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge-Weaver API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
