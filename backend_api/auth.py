"""
Authentication module for Knowledge-Weaver Backend API
Handles API key-based authentication
"""
import os
import logging
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API Key header configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key() -> str:
    """
    Get the configured API key from environment variables
    
    Returns:
        API key string
    
    Raises:
        RuntimeError: If API key is not configured
    """
    api_key = os.getenv("BACKEND_API_KEY")
    if not api_key:
        raise RuntimeError("BACKEND_API_KEY not configured in environment variables")
    return api_key


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header
    
    Args:
        api_key: API key from request header
    
    Returns:
        Validated API key
    
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header in your request."
        )
    
    try:
        expected_key = get_api_key()
    except RuntimeError as e:
        logger.error(f"API key configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    
    if api_key != expected_key:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    logger.debug("API key validated successfully")
    return api_key
