"""Standard response models for API consistency"""

from typing import Optional, Any, List, Dict
from pydantic import BaseModel
from datetime import datetime


class SuccessResponse(BaseModel):
    """Standard success response"""

    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()


class ValidationErrorResponse(BaseModel):
    """Validation error response"""

    success: bool = False
    error: str = "Validation error"
    validation_errors: List[Dict[str, str]]
    timestamp: datetime = datetime.utcnow()


class MessageResponse(BaseModel):
    """Simple message response"""

    message: str


class StatusResponse(BaseModel):
    """Status check response"""

    status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

