"""Event broadcasting service for real-time updates"""

from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict
import asyncio
from datetime import datetime
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class EventService:
    """Service for broadcasting events to subscribers (e.g., for real-time UI updates)"""
    
    def __init__(self):
        # Map of event_type -> list of subscriber callbacks
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # Map of investigation_id -> list of subscriber callbacks
        self._investigation_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # Store recent events for new subscribers (event history)
        self._event_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._max_history = 100  # Keep last 100 events per investigation
    
    def subscribe(
        self,
        event_type: Optional[str] = None,
        investigation_id: Optional[str] = None,
        callback: Optional[Callable] = None
    ):
        """
        Subscribe to events
        
        Args:
            event_type: Specific event type to subscribe to (None = all events)
            investigation_id: Investigation ID to subscribe to (None = all investigations)
            callback: Callback function to call when event occurs
        """
        if investigation_id:
            self._investigation_subscribers[investigation_id].append(callback)
        elif event_type:
            self._subscribers[event_type].append(callback)
        else:
            self._subscribers["*"].append(callback)  # Subscribe to all events
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe a callback from all events"""
        for subscribers in self._subscribers.values():
            if callback in subscribers:
                subscribers.remove(callback)
        for subscribers in self._investigation_subscribers.values():
            if callback in subscribers:
                subscribers.remove(callback)
    
    async def emit(
        self,
        event_type: str,
        data: Dict[str, Any],
        investigation_id: Optional[str] = None
    ):
        """
        Emit an event to all subscribers
        
        Args:
            event_type: Type of event (e.g., 'phase_started', 'evidence_found', 'agent_complete')
            data: Event data
            investigation_id: Optional investigation ID this event relates to
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "investigation_id": investigation_id
        }
        
        # Store in history
        if investigation_id:
            history = self._event_history[investigation_id]
            history.append(event)
            # Keep only last N events
            if len(history) > self._max_history:
                history.pop(0)
        
        logger.info(f"Emitting event: {event_type}", investigation_id=investigation_id, data_keys=list(data.keys()))
        
        # Notify all subscribers
        subscribers_to_notify = []
        
        # Investigation-specific subscribers
        if investigation_id and investigation_id in self._investigation_subscribers:
            subscribers_to_notify.extend(self._investigation_subscribers[investigation_id])
        
        # Event-type-specific subscribers
        if event_type in self._subscribers:
            subscribers_to_notify.extend(self._subscribers[event_type])
        
        # Wildcard subscribers (all events)
        subscribers_to_notify.extend(self._subscribers["*"])
        
        # Call all subscribers
        for callback in subscribers_to_notify:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}", exc_info=True)
    
    def get_event_history(
        self,
        investigation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get event history
        
        Args:
            investigation_id: Optional investigation ID to filter by
            event_type: Optional event type to filter by
            limit: Maximum number of events to return
        
        Returns:
            List of recent events
        """
        if investigation_id:
            events = self._event_history.get(investigation_id, [])
        else:
            # Flatten all investigation histories
            events = []
            for inv_events in self._event_history.values():
                events.extend(inv_events)
            events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        return events[:limit]


# Global event service instance
_event_service: Optional[EventService] = None


def get_event_service() -> EventService:
    """Get global event service instance"""
    global _event_service
    if _event_service is None:
        _event_service = EventService()
    return _event_service

