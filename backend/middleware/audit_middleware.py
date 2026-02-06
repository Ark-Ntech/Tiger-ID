"""Audit middleware for automatic action logging"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
from uuid import UUID

from backend.database import get_db_session
from backend.services.audit_service import get_audit_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log API requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit information"""
        # Skip WebSocket upgrade requests -- BaseHTTPMiddleware cannot handle
        # the WebSocket protocol upgrade and will break the connection.
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Skip logging for certain paths
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Get user ID from request state (set by auth middleware)
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.user_id
        
        # Extract action type from request
        action_type = f"{request.method.lower()}_{request.url.path.replace('/', '_').strip('_')}"
        
        # Get IP and user agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        start_time = time.time()
        status = "success"
        error_message = None
        
        try:
            # Process request
            response = await call_next(request)
            
            # Check if response indicates error
            if response.status_code >= 400:
                status = "failed"
                error_message = f"HTTP {response.status_code}"
            
            # Log audit entry
            try:
                session = get_db_session()
                try:
                    audit_service = get_audit_service(session)

                    # Extract resource info from path
                    resource_type = None
                    resource_id = None

                    path_parts = request.url.path.strip("/").split("/")
                    if len(path_parts) >= 2:
                        resource_type = path_parts[-2] if len(path_parts) >= 2 else None
                        try:
                            resource_id = str(UUID(path_parts[-1]))  # Convert to string for SQLite
                        except (ValueError, IndexError):
                            resource_id = None

                    audit_service.log_action(
                        action_type=action_type,
                        user_id=str(user_id) if user_id else None,  # Convert UUID to string
                        resource_type=resource_type,
                        resource_id=resource_id,
                        action_details={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                            "duration_ms": (time.time() - start_time) * 1000
                        },
                        ip_address=ip_address,
                        user_agent=user_agent,
                        status=status,
                        error_message=error_message
                    )
                finally:
                    session.close()
            except Exception as audit_error:
                logger.error(f"Failed to log audit entry: {audit_error}", exc_info=True)
            
            return response
            
        except Exception as e:
            status = "error"
            error_message = str(e)
            
            # Log error
            try:
                session = get_db_session()
                try:
                    audit_service = get_audit_service(session)
                    audit_service.log_action(
                        action_type=action_type,
                        user_id=str(user_id) if user_id else None,  # Convert UUID to string
                        resource_type=None,
                        resource_id=None,
                        action_details={
                            "method": request.method,
                            "path": request.url.path,
                            "error": str(e)
                        },
                        ip_address=ip_address,
                        user_agent=user_agent,
                        status=status,
                        error_message=error_message
                    )
                finally:
                    session.close()
            except Exception as audit_error:
                logger.error(f"Failed to log audit entry for error: {audit_error}", exc_info=True)

            raise

