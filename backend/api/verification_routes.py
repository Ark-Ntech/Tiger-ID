"""Verification task API routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db, User
from backend.auth.auth import get_current_user
from backend.utils.pagination import PaginatedResponse

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])


@router.get("/tasks")
async def get_verification_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of verification tasks"""
    # For now, return empty list since verification tasks aren't in demo data
    # In production, query from verification_tasks table
    
    paginated = PaginatedResponse.create(
        data=[],
        total=0,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "data": paginated.model_dump()
    }

