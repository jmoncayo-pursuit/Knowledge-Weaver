"""
Knowledge-Weaver Backend API
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

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

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    print("Knowledge-Weaver API starting up...")
    # Vector database initialization will be added here

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge-Weaver API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
