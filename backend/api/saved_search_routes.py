"""API routes for saved searches"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.saved_search_service import get_saved_search_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/saved-searches", tags=["saved-searches"])


class SavedSearchCreate(BaseModel):
    """Saved search creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    search_criteria: Dict[str, Any] = Field(default_factory=dict)
    alert_enabled: bool = False


class SavedSearchUpdate(BaseModel):
    """Saved search update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    search_criteria: Optional[Dict[str, Any]] = None
    alert_enabled: Optional[bool] = None


@router.post("")
async def create_saved_search(
    search_data: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a new saved search"""
    service = get_saved_search_service(db)
    saved_search = service.create_saved_search(
        user_id=current_user.user_id,
        name=search_data.name,
        search_criteria=search_data.search_criteria,
        alert_enabled=search_data.alert_enabled
    )
    
    return {
        "search_id": str(saved_search.search_id),
        "name": saved_search.name,
        "search_criteria": saved_search.search_criteria,
        "alert_enabled": saved_search.alert_enabled,
        "created_at": saved_search.created_at.isoformat() if saved_search.created_at else None
    }


@router.get("")
async def get_saved_searches(
    alert_enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get saved searches for current user"""
    service = get_saved_search_service(db)
    searches = service.get_saved_searches(
        user_id=current_user.user_id,
        alert_enabled=alert_enabled,
        limit=limit,
        offset=offset
    )
    
    return {
        "searches": [
            {
                "search_id": str(s.search_id),
                "name": s.name,
                "search_criteria": s.search_criteria,
                "alert_enabled": s.alert_enabled,
                "last_executed": s.last_executed.isoformat() if s.last_executed else None,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in searches
        ],
        "count": len(searches)
    }


@router.get("/{search_id}")
async def get_saved_search(
    search_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get saved search by ID"""
    service = get_saved_search_service(db)
    saved_search = service.get_saved_search(search_id)
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Check permissions
    if saved_search.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "search_id": str(saved_search.search_id),
        "name": saved_search.name,
        "search_criteria": saved_search.search_criteria,
        "alert_enabled": saved_search.alert_enabled,
        "last_executed": saved_search.last_executed.isoformat() if saved_search.last_executed else None,
        "created_at": saved_search.created_at.isoformat() if saved_search.created_at else None
    }


@router.put("/{search_id}")
async def update_saved_search(
    search_id: UUID,
    search_data: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update saved search"""
    service = get_saved_search_service(db)
    saved_search = service.get_saved_search(search_id)
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Check permissions
    if saved_search.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated = service.update_saved_search(
        search_id=search_id,
        name=search_data.name,
        search_criteria=search_data.search_criteria,
        alert_enabled=search_data.alert_enabled
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    return {
        "search_id": str(updated.search_id),
        "name": updated.name,
        "search_criteria": updated.search_criteria,
        "alert_enabled": updated.alert_enabled
    }


@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete saved search"""
    service = get_saved_search_service(db)
    saved_search = service.get_saved_search(search_id)
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Check permissions
    if saved_search.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = service.delete_saved_search(search_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    return {"message": "Saved search deleted successfully"}


@router.post("/{search_id}/execute")
async def execute_saved_search(
    search_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Execute a saved search"""
    service = get_saved_search_service(db)
    saved_search = service.get_saved_search(search_id)
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Check permissions
    if saved_search.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = service.execute_saved_search(search_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to execute search"))
    
    return result

