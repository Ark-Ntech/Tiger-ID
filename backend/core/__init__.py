"""Core module for Tiger ID.

Contains shared utilities, exceptions, and base classes.
"""

from backend.core.exceptions import (
    TigerIDException,
    TigerNotFoundError,
    InvestigationNotFoundError,
    FacilityNotFoundError,
    UserNotFoundError,
    ModelNotFoundError,
    ModelInferenceError,
    InvestigationWorkflowError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ResourceConflictError,
)

__all__ = [
    "TigerIDException",
    "TigerNotFoundError",
    "InvestigationNotFoundError",
    "FacilityNotFoundError",
    "UserNotFoundError",
    "ModelNotFoundError",
    "ModelInferenceError",
    "InvestigationWorkflowError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "ResourceConflictError",
]
