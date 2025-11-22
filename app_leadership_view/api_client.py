"""
API Client for Knowledge-Weaver Leadership Dashboard
Handles communication with the FastAPI backend
"""
import requests
import streamlit as st
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Client for interacting with Knowledge-Weaver Backend API"""
    
    def __init__(self):
        """Initialize API client with settings from Streamlit secrets"""
        try:
            self.base_url = st.secrets.get("BACKEND_API_URL", "http://localhost:8000")
            self.api_key = st.secrets.get("BACKEND_API_KEY", "dev-secret-key-12345")
        except Exception as e:
            logger.warning(f"Failed to load secrets, using defaults: {e}")
            self.base_url = "http://localhost:8000"
            self.api_key = "dev-secret-key-12345"
        
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        logger.info(f"APIClient initialized with base_url: {self.base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to backend API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
        
        Returns:
            Response data as dictionary
        
        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {endpoint}")
            raise Exception("Request timeout - backend may be slow or unavailable")
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {endpoint}")
            raise Exception("Cannot connect to backend API - please check if it's running")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {endpoint}: {e}")
            if response.status_code == 401:
                raise Exception("Authentication failed - invalid API key")
            elif response.status_code == 404:
                raise Exception("Endpoint not found")
            elif response.status_code == 500:
                raise Exception("Backend server error")
            else:
                raise Exception(f"HTTP {response.status_code}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            raise Exception(f"Request failed: {str(e)}")
    
    def fetch_query_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch query logs from backend for analytics
        
        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of logs to return
        
        Returns:
            List of query log entries
        """
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        try:
            result = self._make_request("GET", "/api/v1/metrics/queries", params=params)
            return result.get("logs", [])
        except Exception as e:
            logger.error(f"Failed to fetch query logs: {e}")
            st.error(f"Failed to fetch query logs: {str(e)}")
            return []
    
    def fetch_unanswered_questions(self) -> List[Dict[str, Any]]:
        """
        Fetch unanswered questions from backend
        
        Returns:
            List of unanswered question entries
        """
        try:
            result = self._make_request("GET", "/api/v1/metrics/unanswered")
            return result.get("unanswered_questions", [])
        except Exception as e:
            logger.error(f"Failed to fetch unanswered questions: {e}")
            st.error(f"Failed to fetch unanswered questions: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test connection to backend API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = self._make_request("GET", "/api/v1/health")
            return result.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get backend health status
        
        Returns:
            Health status dictionary
        """
        try:
            return self._make_request("GET", "/api/v1/health")
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {"status": "error", "message": str(e)}

    def fetch_recent_knowledge(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent knowledge entries
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of knowledge entries
        """
        try:
            return self._make_request("GET", "/api/v1/knowledge/recent", params={"limit": limit})
        except Exception as e:
            logger.error(f"Failed to fetch recent knowledge: {e}")
            return []

    def delete_knowledge_entry(self, entry_id: str) -> bool:
        """Delete a knowledge entry"""
        try:
            response = requests.delete(
                f"{self.base_url}/knowledge/{entry_id}",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting entry: {e}")
            return False

    def update_knowledge_entry(self, entry_id: str, updates: dict) -> bool:
        """Update a knowledge entry"""
        try:
            response = requests.patch(
                f"{self.base_url}/knowledge/{entry_id}",
                headers=self.headers,
                json=updates,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating entry: {e}")
            return False

    def fetch_dashboard_metrics(self) -> dict:
        """Fetch aggregated dashboard metrics"""
        try:
            result = self._make_request("GET", "/api/v1/metrics/dashboard")
            return result
        except Exception as e:
            print(f"Error fetching dashboard metrics: {e}")
            return None
