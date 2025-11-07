"""API routes for global search"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.global_search_service import get_global_search_service
from backend.utils.logging import get_logger
from backend.utils.response_models import SuccessResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("/global")
async def global_search(
    q: str = Query(..., description="Search query"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types (investigations,evidence,facilities,tigers)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results per entity type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform global search across all entities"""
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    entity_type_list = None
    if entity_types:
        entity_type_list = [et.strip() for et in entity_types.split(",")]
    
    service = get_global_search_service(db)
    results = service.search(
        query=q.strip(),
        entity_types=entity_type_list,
        limit=limit,
        user_id=current_user.user_id
    )
    
    return SuccessResponse(
        message=f"Found {results['total_results']} results",
        data=results
    )

