"""FastAPI middleware for rate limiting and security"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict
from collections import defaultdict
from datetime import datetime, timedelta
import time
from backend.utils.logging import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for API endpoints"""
    
    def __init__(self, app, requests_per_minute: int = 60, per_ip: bool = True):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.per_ip = per_ip
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        if self.per_ip:
            client_id = request.client.host if request.client else "unknown"
        else:
            client_id = "global"
        
        # Clean old requests (older than 1 minute)
        now = time.time()
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < 60
        ]
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            logger.warning("Rate limit exceeded", client_id=client_id)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self.requests[client_id].append(now)
        
        # Process request
        response = await call_next(request)
        return response


def sanitize_string_input(value: str, max_length: int = 1000) -> str:
    """Sanitize string input to prevent XSS and SQL injection"""
    if not isinstance(value, str):
        return str(value)
    
    # Remove HTML tags
    import re
    value = re.sub(r'<[^>]+>', '', value)
    
    # Remove script tags and event handlers
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()

