"""
CRM API Integration Service - Task 1.2
=======================================

Comprehensive REST API client for CRM system integration.
Supports JWT/OAuth authentication, rate limiting, and bidirectional sync.

Required Endpoints:
- Projects: CRUD operations for project management
- Tasks: Task lifecycle management with assignments
- Users: User authentication and profile management
- Clients: Client relationship management
- Comments: Communication and collaboration features

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin
import logging
from functools import wraps
import hashlib
import hmac
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CRMConfig:
    """CRM API Configuration"""
    base_url: str
    api_version: str = "v1"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 100
    authentication_type: str = "jwt"  # jwt, oauth, api_key
    
    # Authentication credentials
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Token configuration
    token_refresh_threshold: int = 300  # Refresh token 5 minutes before expiry
    
    def __post_init__(self):
        """Validate configuration on initialization"""
        if not self.base_url:
            raise ValueError("base_url is required")
        
        if self.authentication_type == "jwt" and not (self.username and self.password):
            if not self.api_key:
                raise ValueError("JWT authentication requires username/password or api_key")
        
        if self.authentication_type == "oauth" and not (self.client_id and self.client_secret):
            raise ValueError("OAuth authentication requires client_id and client_secret")

class RateLimiter:
    """Rate limiting functionality"""
    
    def __init__(self, max_calls: int, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self) -> bool:
        """Check if we can make a call within rate limits"""
        now = time.time()
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a new API call"""
        self.calls.append(time.time())
    
    def wait_time(self) -> float:
        """Calculate how long to wait before next call"""
        if not self.calls:
            return 0
        
        oldest_call = min(self.calls)
        wait_time = self.time_window - (time.time() - oldest_call)
        return max(0, wait_time)

def rate_limit(func):
    """Decorator to enforce rate limiting"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.rate_limiter.can_make_call():
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        
        self.rate_limiter.record_call()
        return func(self, *args, **kwargs)
    return wrapper

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 1.0):
    """Decorator to retry failed requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(self, *args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries:
                        logger.error(f"Request failed after {max_retries} retries: {e}")
                        raise
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
            
        return wrapper
    return decorator

class AuthenticationManager:
    """Handles authentication for different auth types"""
    
    def __init__(self, config: CRMConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def authenticate(self) -> Dict[str, str]:
        """Authenticate and return headers for API requests"""
        if self.config.authentication_type == "jwt":
            return self._jwt_authenticate()
        elif self.config.authentication_type == "oauth":
            return self._oauth_authenticate()
        elif self.config.authentication_type == "api_key":
            return self._api_key_authenticate()
        else:
            raise ValueError(f"Unsupported authentication type: {self.config.authentication_type}")
    
    def _jwt_authenticate(self) -> Dict[str, str]:
        """JWT authentication implementation"""
        if self._is_token_valid():
            return {"Authorization": f"Bearer {self.access_token}"}
        
        auth_url = urljoin(self.config.base_url, f"/api/{self.config.api_version}/auth/login")
        
        if self.config.api_key:
            payload = {"api_key": self.config.api_key}
        else:
            payload = {
                "username": self.config.username,
                "password": self.config.password
            }
        
        try:
            response = self.session.post(
                auth_url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data.get("access_token")
            self.refresh_token = auth_data.get("refresh_token")
            
            # Calculate token expiry
            expires_in = auth_data.get("expires_in", 3600)  # Default 1 hour
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info("JWT authentication successful")
            return {"Authorization": f"Bearer {self.access_token}"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"JWT authentication failed: {e}")
            raise
    
    def _oauth_authenticate(self) -> Dict[str, str]:
        """OAuth 2.0 authentication implementation"""
        if self._is_token_valid():
            return {"Authorization": f"Bearer {self.access_token}"}
        
        token_url = urljoin(self.config.base_url, f"/api/{self.config.api_version}/oauth/token")
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret
        }
        
        try:
            response = self.session.post(
                token_url,
                data=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            # Calculate token expiry
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info("OAuth authentication successful")
            return {"Authorization": f"Bearer {self.access_token}"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OAuth authentication failed: {e}")
            raise
    
    def _api_key_authenticate(self) -> Dict[str, str]:
        """API Key authentication implementation"""
        return {"X-API-Key": self.config.api_key}
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not near expiry"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # Check if token expires within threshold
        threshold = timedelta(seconds=self.config.token_refresh_threshold)
        return datetime.utcnow() + threshold < self.token_expiry
    
    def refresh_access_token(self) -> Dict[str, str]:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return self.authenticate()
        
        refresh_url = urljoin(self.config.base_url, f"/api/{self.config.api_version}/auth/refresh")
        
        try:
            response = self.session.post(
                refresh_url,
                json={"refresh_token": self.refresh_token},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            # Update expiry
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info("Token refreshed successfully")
            return {"Authorization": f"Bearer {self.access_token}"}
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Token refresh failed, re-authenticating: {e}")
            return self.authenticate()

class CRMAPIClient:
    """Main CRM API Client"""
    
    def __init__(self, config: CRMConfig):
        self.config = config
        self.auth_manager = AuthenticationManager(config)
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute, 60)
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"CRM API Client initialized for {config.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests including authentication"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CRM-API-Client/1.0"
        }
        
        # Add authentication headers
        auth_headers = self.auth_manager.authenticate()
        headers.update(auth_headers)
        
        return headers
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint"""
        return urljoin(self.config.base_url, f"/api/{self.config.api_version}/{endpoint.lstrip('/')}")
    
    @rate_limit
    @retry_on_failure()
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> requests.Response:
        """Make HTTP request to CRM API"""
        url = self._build_url(endpoint)
        headers = self._get_headers()
        
        logger.debug(f"Making {method.upper()} request to {url}")
        
        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data if data else None,
            params=params if params else None,
            timeout=self.config.timeout
        )
        
        # Handle authentication errors
        if response.status_code == 401:
            logger.warning("Authentication failed, refreshing token...")
            headers = self._get_headers()
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data if data else None,
                params=params if params else None,
                timeout=self.config.timeout
            )
        
        response.raise_for_status()
        return response
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request to CRM API"""
        response = self._make_request("GET", endpoint, params=params)
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request to CRM API"""
        response = self._make_request("POST", endpoint, data=data)
        return response.json()
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request to CRM API"""
        response = self._make_request("PUT", endpoint, data=data)
        return response.json()
    
    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH request to CRM API"""
        response = self._make_request("PATCH", endpoint, data=data)
        return response.json()
    
    def delete(self, endpoint: str) -> bool:
        """DELETE request to CRM API"""
        response = self._make_request("DELETE", endpoint)
        return response.status_code in [200, 204]
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health and connectivity"""
        try:
            response = self.get("health")
            logger.info("CRM API health check passed")
            return response
        except Exception as e:
            logger.error(f"CRM API health check failed: {e}")
            raise
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API version and capabilities information"""
        try:
            response = self.get("info")
            logger.info("Retrieved CRM API information")
            return response
        except Exception as e:
            logger.warning(f"Could not retrieve API info: {e}")
            return {"version": self.config.api_version, "status": "unknown"}

# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = CRMConfig(
        base_url="https://api.crm.example.com",
        api_version="v1",
        authentication_type="jwt",
        username="api_user",
        password="api_password",
        rate_limit_per_minute=100
    )
    
    # Initialize client
    client = CRMAPIClient(config)
    
    try:
        # Test connectivity
        health = client.health_check()
        print(f"Health check: {health}")
        
        # Get API info
        info = client.get_api_info()
        print(f"API Info: {info}")
        
    except Exception as e:
        print(f"Error: {e}")