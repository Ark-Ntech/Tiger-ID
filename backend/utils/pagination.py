"""Pagination utilities for API responses"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from math import ceil

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination"""

    page: int = 1
    page_size: int = 20
    
    def get_offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size
    
    def get_limit(self) -> int:
        """Get limit for database query"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response"""

    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response"""
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response envelope"""

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def success_response(
        cls, data: T, message: Optional[str] = None
    ) -> "ApiResponse[T]":
        """Create a success response"""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(
        cls, error: str, message: Optional[str] = None
    ) -> "ApiResponse":
        """Create an error response"""
        return cls(success=False, error=error, message=message)


def paginate_query(query, page: int = 1, page_size: int = 20):
    """
    Helper to paginate SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        tuple: (items, total_count)
    """
    # Get total count
    total = query.count()
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get paginated items
    items = query.offset(offset).limit(page_size).all()
    
    return items, total

