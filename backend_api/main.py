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

# Global vector database instance
vector_db: VectorDatabase = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    global vector_db
    
    logger.info("Knowledge-Weaver API starting up...")
    
    # Initialize Vector Database
    try:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        vector_db = VectorDatabase(persist_directory=persist_dir)
        vector_db.initialize()
        
        stats = vector_db.get_collection_stats()
        logger.info(f"Vector Database initialized: {stats}")
    except Exception as e:
        logger.error(f"Failed to initialize Vector Database: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge-Weaver API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
