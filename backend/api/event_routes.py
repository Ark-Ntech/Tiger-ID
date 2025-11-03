"""API routes for fetching investigation events"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from uuid import UUID

from backend.auth.auth import get_current_user
from backend.database import User
from backend.services.event_service import get_event_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("/investigation/{investigation_id}")
async def get_investigation_events(
    investigation_id: UUID,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of events"),
    current_user: User = Depends(get_current_user)
):
    """
    Get event history for an investigation
    
    Args:
        investigation_id: Investigation ID
        event_type: Optional event type filter
        limit: Maximum number of events to return
        current_user: Current authenticated user
    
    Returns:
        List of events
    """
    event_service = get_event_service()
    events = event_service.get_event_history(
        investigation_id=str(investigation_id),
        event_type=event_type,
        limit=limit
    )
    
    return {
        "investigation_id": str(investigation_id),
        "events": events,
        "count": len(events)
    }


@router.get("/latest")
async def get_latest_events(
    investigation_id: Optional[str] = Query(None, description="Filter by investigation ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of events"),
    current_user: User = Depends(get_current_user)
):
    """
    Get latest events across all investigations or filtered by investigation
    
    Args:
        investigation_id: Optional investigation ID filter
        event_type: Optional event type filter
        limit: Maximum number of events to return
        current_user: Current authenticated user
    
    Returns:
        List of latest events
    """
    event_service = get_event_service()
    events = event_service.get_event_history(
        investigation_id=investigation_id,
        event_type=event_type,
        limit=limit
    )
    
    return {
        "events": events,
        "count": len(events)
    }

