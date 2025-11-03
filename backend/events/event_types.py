"""Event type definitions for the investigation system"""

from enum import Enum
from typing import Dict, Any, Optional


class EventType(str, Enum):
    """Standard event types for investigation workflow"""
    
    # Investigation lifecycle events
    INVESTIGATION_STARTED = "investigation_started"
    INVESTIGATION_PAUSED = "investigation_paused"
    INVESTIGATION_RESUMED = "investigation_resumed"
    INVESTIGATION_CANCELLED = "investigation_cancelled"
    INVESTIGATION_COMPLETED = "investigation_completed"
    
    # Phase events
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_FAILED = "phase_failed"
    
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_ACTIVITY = "agent_activity"
    
    # Evidence events
    EVIDENCE_FOUND = "evidence_found"
    EVIDENCE_ADDED = "evidence_added"
    EVIDENCE_UPDATED = "evidence_updated"
    
    # Progress events
    PROGRESS_UPDATE = "progress_update"
    STEP_COMPLETED = "step_completed"
    
    # Error events
    ERROR_OCCURRED = "error_occurred"
    WARNING = "warning"
    
    # Notification events
    NOTIFICATION = "notification"
    HIGH_PRIORITY_FINDING = "high_priority_finding"
    
    # Human-in-the-loop events
    HUMAN_INPUT_REQUESTED = "human_input_requested"
    HUMAN_INPUT_RECEIVED = "human_input_received"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RECEIVED = "approval_received"


def create_event(
    event_type: EventType,
    data: Dict[str, Any],
    investigation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized event dictionary
    
    Args:
        event_type: Type of event
        data: Event-specific data
        investigation_id: Optional investigation ID
    
    Returns:
        Standardized event dictionary
    """
    from datetime import datetime
    
    return {
        "event_type": event_type.value if isinstance(event_type, EventType) else event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
        "investigation_id": investigation_id
    }

