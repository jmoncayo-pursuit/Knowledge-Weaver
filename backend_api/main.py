"""
Knowledge-Weaver Backend API
Main application entry point
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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

# Configure CORS - Explicit configuration for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - configure for production with specific domains
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers including X-API-Key
    expose_headers=["*"],  # Expose all headers to the client
)

# Include API router
app.include_router(api.router)


# Global Exception Handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors"""
    logger.warning(f"404 Not Found: {request.url}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "detail": f"The requested resource at {request.url.path} was not found",
            "status_code": 404
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """Handle 500 Internal Server Error"""
    logger.error(f"500 Internal Server Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "status_code": 500
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "status_code": 500
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "status_code": 422
        }
    )


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
