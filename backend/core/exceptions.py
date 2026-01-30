"""Custom exceptions for Tiger ID.

This module provides a hierarchy of exceptions for standardized error handling
across the application. All custom exceptions inherit from TigerIDException.
"""

from typing import Optional, Dict, Any
from http import HTTPStatus


class TigerIDException(Exception):
    """Base exception for all Tiger ID errors.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code
        details: Additional error details
        status_code: HTTP status code for API responses
    """

    def __init__(
        self,
        message: str,
        code: str = "TIGER_ID_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
            "success": False,
        }


# ==================== Not Found Exceptions ====================

class NotFoundError(TigerIDException):
    """Base class for resource not found errors."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"{resource_type} with ID '{resource_id}' not found"

        super().__init__(
            message=message,
            code=f"{resource_type.upper()}_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                **(details or {})
            },
            status_code=HTTPStatus.NOT_FOUND
        )


class TigerNotFoundError(NotFoundError):
    """Raised when a tiger is not found."""

    def __init__(
        self,
        tiger_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            resource_type="Tiger",
            resource_id=tiger_id,
            message=message,
            details=details
        )


class InvestigationNotFoundError(NotFoundError):
    """Raised when an investigation is not found."""

    def __init__(
        self,
        investigation_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            resource_type="Investigation",
            resource_id=investigation_id,
            message=message,
            details=details
        )


class FacilityNotFoundError(NotFoundError):
    """Raised when a facility is not found."""

    def __init__(
        self,
        facility_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            resource_type="Facility",
            resource_id=facility_id,
            message=message,
            details=details
        )


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""

    def __init__(
        self,
        user_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            resource_type="User",
            resource_id=user_id,
            message=message,
            details=details
        )


# ==================== Model Exceptions ====================

class ModelNotFoundError(TigerIDException):
    """Raised when a requested ML model is not available."""

    def __init__(
        self,
        model_name: str,
        available_models: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Model '{model_name}' not found or not available",
            code="MODEL_NOT_FOUND",
            details={
                "model_name": model_name,
                "available_models": available_models or [],
                **(details or {})
            },
            status_code=HTTPStatus.NOT_FOUND
        )


class ModelInferenceError(TigerIDException):
    """Raised when model inference fails."""

    def __init__(
        self,
        model_name: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Inference failed for model '{model_name}'"

        super().__init__(
            message=message,
            code="MODEL_INFERENCE_ERROR",
            details={
                "model_name": model_name,
                **(details or {})
            },
            status_code=HTTPStatus.SERVICE_UNAVAILABLE
        )


# ==================== Workflow Exceptions ====================

class InvestigationWorkflowError(TigerIDException):
    """Raised when investigation workflow encounters an error."""

    def __init__(
        self,
        investigation_id: str,
        phase: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Investigation workflow error for '{investigation_id}'"
            if phase:
                message += f" at phase '{phase}'"

        super().__init__(
            message=message,
            code="INVESTIGATION_WORKFLOW_ERROR",
            details={
                "investigation_id": investigation_id,
                "phase": phase,
                **(details or {})
            },
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )


# ==================== Auth Exceptions ====================

class AuthenticationError(TigerIDException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details,
            status_code=HTTPStatus.UNAUTHORIZED
        )


class AuthorizationError(TigerIDException):
    """Raised when authorization fails (user lacks permission)."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details={
                "required_permission": required_permission,
                **(details or {})
            },
            status_code=HTTPStatus.FORBIDDEN
        )


# ==================== Validation Exceptions ====================

class ValidationError(TigerIDException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={
                "field": field,
                **(details or {})
            },
            status_code=HTTPStatus.BAD_REQUEST
        )


class ResourceConflictError(TigerIDException):
    """Raised when a resource conflict occurs (e.g., duplicate)."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="RESOURCE_CONFLICT",
            details={
                "resource_type": resource_type,
                **(details or {})
            },
            status_code=HTTPStatus.CONFLICT
        )


# ==================== Exception Handlers ====================

def create_exception_handlers():
    """Create FastAPI exception handlers for custom exceptions.

    Returns:
        Dictionary of exception type to handler function
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse

    async def tiger_id_exception_handler(
        request: Request,
        exc: TigerIDException
    ) -> JSONResponse:
        """Handle TigerIDException and subclasses."""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )

    return {
        TigerIDException: tiger_id_exception_handler
    }


def register_exception_handlers(app):
    """Register all exception handlers with a FastAPI app.

    Args:
        app: FastAPI application instance
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(TigerIDException)
    async def tiger_id_exception_handler(
        request: Request,
        exc: TigerIDException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )

    # Also handle generic exceptions
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        # Log the error
        import logging
        logging.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {}
                },
                "success": False
            }
        )
