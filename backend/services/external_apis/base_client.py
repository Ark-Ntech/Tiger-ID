"""Base API client with common functionality"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
from abc import ABC, abstractmethod

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class BaseAPIClient(ABC):
    """Base class for external API clients"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "",
        timeout: int = 30,
        rate_limit_delay: float = 0.5,
        max_retries: int = 3
    ):
        """
        Initialize API client
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between requests (seconds)
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.last_request_time = 0.0
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        return headers
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            headers: Additional headers
        
        Returns:
            Response data as dictionary
        
        Raises:
            httpx.HTTPStatusError: On HTTP error
            Exception: On other errors
        """
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=data,
                        headers=request_headers
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 2
                    logger.warning(
                        "Rate limited, waiting",
                        wait_time=wait_time,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep(wait_time)
                    continue
                elif e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    logger.warning(
                        "Server error, retrying",
                        status_code=e.response.status_code,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep((attempt + 1) * 1)
                    continue
                else:
                    logger.error(
                        "HTTP error",
                        status_code=e.response.status_code,
                        response=e.response.text
                    )
                    raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "Request failed, retrying",
                        error=str(e),
                        attempt=attempt + 1
                    )
                    await asyncio.sleep((attempt + 1) * 1)
                    continue
                else:
                    logger.error("Request failed after retries", error=str(e))
                    raise
        
        raise Exception("Request failed after all retries")
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if API is accessible"""
        pass
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        try:
            is_healthy = await self.health_check()
            return {
                "status": "connected" if is_healthy else "disconnected",
                "base_url": self.base_url,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "base_url": self.base_url,
                "timestamp": datetime.utcnow().isoformat()
            }

