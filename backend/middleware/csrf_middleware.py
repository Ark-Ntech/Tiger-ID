"""CSRF protection middleware"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import secrets
from datetime import datetime, timedelta

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection"""
    
    def __init__(self, app, secret_key: str = None, token_lifetime: int = 3600):
        """
        Initialize CSRF middleware
        
        Args:
            app: FastAPI application
            secret_key: Secret key for token generation (defaults to random)
            token_lifetime: Token lifetime in seconds (default 1 hour)
        """
        super().__init__(app)
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.token_lifetime = token_lifetime
        self.token_store = {}  # In production, use Redis or database
    
    def generate_csrf_token(self) -> str:
        """Generate a new CSRF token"""
        token = secrets.token_urlsafe(32)
        self.token_store[token] = datetime.utcnow() + timedelta(seconds=self.token_lifetime)
        return token
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate a CSRF token"""
        if not token:
            return False
        
        if token not in self.token_store:
            return False
        
        expiry = self.token_store[token]
        if datetime.utcnow() > expiry:
            del self.token_store[token]
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with CSRF protection"""
        # Skip WebSocket upgrade requests -- BaseHTTPMiddleware cannot handle
        # the WebSocket protocol upgrade and will break the connection.
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Skip CSRF for safe methods and certain paths
        safe_methods = ["GET", "HEAD", "OPTIONS"]
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc", "/api/auth"]
        
        if request.method in safe_methods or any(request.url.path.startswith(path) for path in skip_paths):
            response = await call_next(request)
            # Add CSRF token to response headers for GET requests
            if request.method == "GET":
                csrf_token = self.generate_csrf_token()
                response.headers["X-CSRF-Token"] = csrf_token
            return response
        
        # For state-changing methods, check CSRF token
        csrf_token = request.headers.get("X-CSRF-Token") or request.headers.get("X-Csrf-Token")
        
        if not csrf_token:
            # Try to get from form data
            content_type = request.headers.get("content-type", "")
            if content_type and content_type.startswith("application/x-www-form-urlencoded"):
                form = await request.form()
                csrf_token = form.get("csrf_token")
        
        if not self.validate_csrf_token(csrf_token):
            logger.warning(f"CSRF token validation failed for {request.method} {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token validation failed"
            )
        
        response = await call_next(request)
        
        # Generate new token for response
        new_token = self.generate_csrf_token()
        response.headers["X-CSRF-Token"] = new_token
        
        return response
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens (call periodically)"""
        now = datetime.utcnow()
        expired = [token for token, expiry in self.token_store.items() if now > expiry]
        for token in expired:
            del self.token_store[token]

