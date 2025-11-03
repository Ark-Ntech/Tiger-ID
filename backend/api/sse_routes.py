"""Server-Sent Events (SSE) routes for real-time updates"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from uuid import UUID
import asyncio
import json
from datetime import datetime

from backend.auth.auth import get_current_user
from backend.database import User
from backend.services.event_service import get_event_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/sse", tags=["sse"])


async def event_stream(investigation_id: Optional[str] = None):
    """
    Generate SSE event stream
    
    Args:
        investigation_id: Optional investigation ID to filter events
    """
    event_service = get_event_service()
    last_event_time = datetime.utcnow()
    
    # Send initial connection event
    yield f"data: {json.dumps({'event_type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    
    # Subscribe to events
    events_queue = asyncio.Queue()
    
    async def event_callback(event: dict):
        """Callback for events"""
        await events_queue.put(event)
    
    # Subscribe based on investigation_id
    if investigation_id:
        event_service.subscribe(investigation_id=str(investigation_id), callback=event_callback)
    else:
        event_service.subscribe(callback=event_callback)
    
    try:
        # Send event history first
        history = event_service.get_event_history(investigation_id=investigation_id, limit=20)
        for event in history:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Listen for new events
        while True:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(events_queue.get(), timeout=30.0)
                
                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"
                last_event_time = datetime.utcnow()
                
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield f": heartbeat\n\n"
                
    except asyncio.CancelledError:
        logger.info("SSE connection cancelled", investigation_id=investigation_id)
    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
    finally:
        # Unsubscribe
        event_service.unsubscribe(event_callback)


@router.get("/events")
async def stream_events(
    investigation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Stream investigation events via Server-Sent Events (SSE)
    
    Args:
        investigation_id: Optional investigation ID to filter events
        current_user: Current authenticated user
    
    Returns:
        SSE event stream
    """
    return StreamingResponse(
        event_stream(investigation_id=investigation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

