"""Error type definitions for structured error handling"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class ErrorCategory(str, Enum):
    """Error categories"""
    RECOVERABLE = "recoverable"  # Can retry or continue
    FATAL = "fatal"  # Cannot recover, must stop
    RETRYABLE = "retryable"  # Can retry with backoff
    VALIDATION = "validation"  # Input validation error
    AUTHORIZATION = "authorization"  # Permission error
    NETWORK = "network"  # Network-related error
    DATABASE = "database"  # Database error
    EXTERNAL_API = "external_api"  # External API error
    AGENT = "agent"  # Agent-specific error
    MODEL = "model"  # ML model error


@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    category: ErrorCategory
    message: str
    details: Optional[Dict[str, Any]] = None
    recovery_options: Optional[list] = None
    retry_count: int = 0
    max_retries: int = 3
    can_retry: bool = True
    
    def __post_init__(self):
        """Set defaults based on category"""
        if self.category == ErrorCategory.FATAL:
            self.can_retry = False
            self.max_retries = 0
        elif self.category == ErrorCategory.RETRYABLE:
            self.can_retry = True
        elif self.category == ErrorCategory.RECOVERABLE:
            self.can_retry = True
        else:
            self.can_retry = False


def create_error(
    category: ErrorCategory,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    recovery_options: Optional[list] = None,
    error_id: Optional[str] = None
) -> ErrorInfo:
    """
    Create a structured error
    
    Args:
        category: Error category
        message: Error message
        details: Optional error details
        recovery_options: Optional recovery actions
        error_id: Optional error ID
    
    Returns:
        ErrorInfo object
    """
    import uuid
    
    return ErrorInfo(
        error_id=error_id or str(uuid.uuid4()),
        category=category,
        message=message,
        details=details or {},
        recovery_options=recovery_options or []
    )

