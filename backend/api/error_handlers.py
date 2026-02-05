"""Standardized error handling for the backend API.

This module provides a consistent error handling pattern across all API endpoints.
All custom exceptions inherit from APIError and are automatically converted to
JSON responses with a standard format.

Response format:
{
    "error": "Human-readable error message",
    "code": "MACHINE_READABLE_ERROR_CODE",
    "status": 404
}
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error with status code and optional error code.

    All custom API exceptions should inherit from this class.
    The api_error_handler will automatically convert these to JSON responses.

    Args:
        status_code: HTTP status code (e.g., 404, 422, 500)
        detail: Human-readable error message
        error_code: Machine-readable error code (e.g., "NOT_FOUND")
        headers: Optional headers to include in the response

    Example:
        raise APIError(400, "Invalid input", "INVALID_INPUT")
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.headers = headers
        super().__init__(detail)


class NotFoundError(APIError):
    """Resource not found error (HTTP 404).

    Use when a requested resource does not exist.

    Example:
        raise NotFoundError("Tiger", "TIG-001")
        # Results in: {"error": "Tiger 'TIG-001' not found", "code": "NOT_FOUND", "status": 404}
    """

    def __init__(self, resource: str, identifier: str):
        super().__init__(404, f"{resource} '{identifier}' not found", "NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class ValidationError(APIError):
    """Validation error (HTTP 422).

    Use when request data fails validation.

    Example:
        raise ValidationError("Image must be at least 224x224 pixels")
    """

    def __init__(self, detail: str):
        super().__init__(422, detail, "VALIDATION_ERROR")


class AuthenticationError(APIError):
    """Authentication error (HTTP 401).

    Use when authentication is required but not provided or invalid.

    Example:
        raise AuthenticationError("Token has expired")
    """

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(401, detail, "AUTHENTICATION_ERROR")


class AuthorizationError(APIError):
    """Authorization error (HTTP 403).

    Use when the user is authenticated but lacks permission for the action.

    Example:
        raise AuthorizationError("Admin role required to delete tigers")
    """

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(403, detail, "AUTHORIZATION_ERROR")


class ConflictError(APIError):
    """Conflict error (HTTP 409).

    Use when the request conflicts with the current state of the resource.

    Example:
        raise ConflictError("Tiger with this ID already exists")
    """

    def __init__(self, detail: str):
        super().__init__(409, detail, "CONFLICT")


class RateLimitError(APIError):
    """Rate limit exceeded error (HTTP 429).

    Use when a client has exceeded their rate limit.

    Example:
        raise RateLimitError("Rate limit exceeded. Try again in 60 seconds.")
    """

    def __init__(self, detail: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        super().__init__(429, detail, "RATE_LIMIT_EXCEEDED", headers=headers)


class ServiceUnavailableError(APIError):
    """Service unavailable error (HTTP 503).

    Use when a dependent service is unavailable.

    Example:
        raise ServiceUnavailableError("Modal GPU service is currently unavailable")
    """

    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(503, detail, "SERVICE_UNAVAILABLE")


class BadRequestError(APIError):
    """Bad request error (HTTP 400).

    Use for general bad request errors that don't fit validation errors.

    Example:
        raise BadRequestError("Missing required file upload")
    """

    def __init__(self, detail: str):
        super().__init__(400, detail, "BAD_REQUEST")


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions and convert to JSON responses.

    This handler is registered with FastAPI to catch all APIError exceptions
    and their subclasses, converting them to a standardized JSON response format.

    Args:
        request: The incoming request
        exc: The APIError exception

    Returns:
        JSONResponse with standardized error format
    """
    logger.warning(
        f"API error: {exc.error_code} - {exc.detail} "
        f"[{request.method} {request.url.path}]"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": exc.error_code,
            "status": exc.status_code
        },
        headers=exc.headers
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with a generic error response.

    This handler catches all unhandled exceptions and returns a safe
    generic error message without exposing internal details.
    The full exception is logged for debugging.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        JSONResponse with generic 500 error
    """
    logger.exception(
        f"Unexpected error on {request.method} {request.url.path}: {exc}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "status": 500
        }
    )
