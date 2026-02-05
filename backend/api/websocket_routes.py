"""WebSocket routes for real-time communication"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional, Dict, List
import asyncio
import json
from datetime import datetime
from backend.auth.auth import get_current_user_ws
from backend.services.websocket_service import get_websocket_manager
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Subagent Progress Tracking Functions
# =============================================================================
# These functions emit WebSocket events for tracking subagent execution during
# investigation workflows. They are used by the investigation workflow to
# provide real-time progress updates to connected clients.


async def emit_to_investigation(investigation_id: str, message: dict) -> None:
    """
    Emit a message to all clients subscribed to an investigation.

    Args:
        investigation_id: The investigation ID to broadcast to.
        message: The message dictionary to send.
    """
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast_to_investigation(message, investigation_id)


async def emit_subagent_spawned(
    investigation_id: str,
    subagent_id: str,
    subagent_type: str,
    phase: str
) -> None:
    """
    Emit event when a subagent is spawned.

    Args:
        investigation_id: The investigation this subagent belongs to.
        subagent_id: Unique identifier for the subagent instance.
        subagent_type: Type of subagent (e.g., 'reverse_image_search', 'stripe_analysis').
        phase: Current workflow phase (e.g., 'tiger_detection', 'stripe_analysis').
    """
    await emit_to_investigation(investigation_id, {
        "event": "subagent_spawned",
        "data": {
            "subagent_id": subagent_id,
            "subagent_type": subagent_type,
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    logger.debug(f"Subagent spawned: {subagent_type} ({subagent_id}) for investigation {investigation_id}")


async def emit_subagent_progress(
    investigation_id: str,
    subagent_id: str,
    progress: int,
    message: Optional[str] = None
) -> None:
    """
    Emit subagent progress update.

    Args:
        investigation_id: The investigation this subagent belongs to.
        subagent_id: Unique identifier for the subagent instance.
        progress: Progress percentage (0-100).
        message: Optional status message describing current activity.
    """
    await emit_to_investigation(investigation_id, {
        "event": "subagent_progress",
        "data": {
            "subagent_id": subagent_id,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    logger.debug(f"Subagent progress: {subagent_id} at {progress}% - {message}")


async def emit_subagent_completed(
    investigation_id: str,
    subagent_id: str,
    result: Optional[dict] = None
) -> None:
    """
    Emit event when subagent completes successfully.

    Args:
        investigation_id: The investigation this subagent belongs to.
        subagent_id: Unique identifier for the subagent instance.
        result: Optional result data from the subagent execution.
    """
    await emit_to_investigation(investigation_id, {
        "event": "subagent_completed",
        "data": {
            "subagent_id": subagent_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    logger.debug(f"Subagent completed: {subagent_id} for investigation {investigation_id}")


async def emit_subagent_error(
    investigation_id: str,
    subagent_id: str,
    error: str
) -> None:
    """
    Emit event when subagent fails with an error.

    Args:
        investigation_id: The investigation this subagent belongs to.
        subagent_id: Unique identifier for the subagent instance.
        error: Error message describing the failure.
    """
    await emit_to_investigation(investigation_id, {
        "event": "subagent_error",
        "data": {
            "subagent_id": subagent_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    logger.warning(f"Subagent error: {subagent_id} - {error}")


async def emit_model_progress(
    investigation_id: str,
    model_name: str,
    progress: int,
    status: str = "running"
) -> None:
    """
    Emit per-model progress for stripe analysis phase.

    This is used during the stripe_analysis phase to track individual model
    progress in the 6-model ensemble.

    Args:
        investigation_id: The investigation ID.
        model_name: Name of the model (e.g., 'wildlife_tools', 'cvwc2019_reid').
        progress: Progress percentage (0-100).
        status: Model status ('running', 'completed', 'error', 'pending').
    """
    await emit_to_investigation(investigation_id, {
        "event": "model_progress",
        "data": {
            "model": model_name,
            "progress": progress,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    logger.debug(f"Model progress: {model_name} at {progress}% ({status})")


# Export subagent tracking functions for use by investigation workflow
__all__ = [
    "router",
    "emit_to_investigation",
    "emit_subagent_spawned",
    "emit_subagent_progress",
    "emit_subagent_completed",
    "emit_subagent_error",
    "emit_model_progress",
]

# Locks for preventing race conditions on investigation operations
# One lock per investigation to allow concurrent work on different investigations
_investigation_locks: Dict[str, asyncio.Lock] = {}
_locks_lock = asyncio.Lock()  # Lock to protect the locks dictionary


async def get_investigation_lock(investigation_id: str) -> asyncio.Lock:
    """Get or create a lock for a specific investigation."""
    async with _locks_lock:
        if investigation_id not in _investigation_locks:
            _investigation_locks[investigation_id] = asyncio.Lock()
        return _investigation_locks[investigation_id]


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time communication
    
    Connect with: ws://localhost:8000/ws?token=YOUR_JWT_TOKEN
    """
    logger.info(f"WebSocket connection attempt received. Token present: {token is not None}")
    ws_manager = get_websocket_manager()
    
    # Accept connection
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    # Authenticate user
    user_uuid = None
    try:
        if not token:
            logger.warning("WebSocket connection rejected: No token provided")
            await websocket.send_json({
                "type": "error",
                "message": "Authentication required"
            })
            await websocket.close()
            return
        
        # Properly decode JWT token
        from backend.auth.auth import get_current_user_ws
        from backend.database import get_db_session
        
        # Get user from token
        db = next(get_db_session())
        try:
            user = await get_current_user_ws(token, db)
            if not user:
                logger.warning("WebSocket connection rejected: Invalid or expired token")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid or expired token"
                })
                await websocket.close()
                return
            
            user_id = str(user.user_id)
            user_uuid = user.user_id
        finally:
            db.close()
        
        logger.info(f"WebSocket authenticated for user: {user_id}")
        
        # Register connection
        await ws_manager.connect(websocket, user_id)
        
        # Send connection success message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected successfully",
            "user_id": user_id,
        })
        
        logger.info(f"WebSocket connection established for user: {user_id}")
        
        # Listen for messages
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif message_type == "join_investigation":
                    investigation_id = message.get("investigation_id")
                    if investigation_id:
                        await ws_manager.join_investigation(websocket, investigation_id)
                        await websocket.send_json({
                            "type": "joined_investigation",
                            "investigation_id": investigation_id,
                        })
                
                elif message_type == "leave_investigation":
                    investigation_id = message.get("investigation_id")
                    if investigation_id:
                        await ws_manager.leave_investigation(websocket, investigation_id)
                        await websocket.send_json({
                            "type": "left_investigation",
                            "investigation_id": investigation_id,
                        })
                
                elif message_type == "chat_message":
                    # Handle chat messages with orchestrator integration
                    investigation_id = message.get("investigation_id")
                    content = message.get("content")
                    selected_tools = message.get("selected_tools", [])

                    tiger_id_value = message.get("tiger_id")

                    if investigation_id and content:
                        from uuid import UUID
                        from backend.services.investigation_service import InvestigationService
                        from backend.database import get_db_session
                        from backend.database.models import User

                        try:
                            # Ensure user_uuid is set (should be from authentication)
                            if not user_uuid:
                                logger.error("user_uuid not set - authentication may have failed")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Authentication error. Please reconnect."
                                })
                                continue

                            # Get lock for this investigation to prevent race conditions
                            inv_lock = await get_investigation_lock(investigation_id)

                            async with inv_lock:
                                # Process message with Hermes chat orchestrator
                                db = next(get_db_session())
                                try:
                                    investigation_service = InvestigationService(db)

                                    logger.info(f"Processing chat message for investigation {investigation_id} with {len(selected_tools) if selected_tools else 0} selected tools")

                                    # Launch investigation with the chat message
                                    result = await investigation_service.launch_investigation(
                                        investigation_id=UUID(investigation_id),
                                        user_input=content,
                                        files=[],
                                        user_id=user_uuid,
                                        selected_tools=selected_tools if selected_tools else None,
                                        tiger_id=tiger_id_value
                                    )

                                    logger.info(f"Investigation launched successfully. Response: {result.get('response', '')[:100]}")

                                    # Send assistant response
                                    assistant_response = result.get("response", "I've processed your request. Let me investigate this for you.")

                                    await ws_manager.broadcast_to_investigation(
                                        {
                                            "type": "chat_message",
                                            "data": {
                                                "id": str(UUID(int=0)),
                                                "role": "assistant",
                                                "content": assistant_response,
                                                "timestamp": datetime.utcnow().isoformat(),
                                                "agent_type": "orchestrator"
                                            },
                                            "investigation_id": investigation_id,
                                        },
                                        investigation_id,
                                    )

                                    # Also echo the user message
                                    await ws_manager.broadcast_to_investigation(
                                        {
                                            "type": "chat_message",
                                            "data": {
                                                "id": str(UUID(int=1)),
                                                "role": "user",
                                                "content": content,
                                                "timestamp": datetime.utcnow().isoformat(),
                                            },
                                            "investigation_id": investigation_id,
                                        },
                                        investigation_id,
                                    )
                                finally:
                                    db.close()
                        except Exception as e:
                            error_type = type(e).__name__
                            error_msg = str(e)
                            # Log detailed error for debugging (server-side only)
                            logger.error(f"Error processing chat message ({error_type}): {error_msg}", exc_info=True)

                            # Determine user-friendly message without exposing internals
                            if "Modal" in error_msg or "modal" in error_msg.lower():
                                user_friendly_error = "The ML service is temporarily unavailable. Please try again later."
                            elif "authentication" in error_msg.lower() or "auth" in error_msg.lower():
                                user_friendly_error = "Your session has expired. Please reconnect."
                            elif "timeout" in error_msg.lower():
                                user_friendly_error = "The request timed out. Please try again with a smaller image or simpler query."
                            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                                user_friendly_error = "A connection error occurred. Please check your network and try again."
                            elif "database" in error_msg.lower() or "sql" in error_msg.lower():
                                user_friendly_error = "A database error occurred. Please try again later."
                            else:
                                user_friendly_error = "An unexpected error occurred. Please try again."

                            # Send sanitized error message to chat (no internal details)
                            await ws_manager.broadcast_to_investigation(
                                {
                                    "type": "chat_message",
                                    "data": {
                                        "id": str(UUID(int=0)),
                                        "role": "assistant",
                                        "content": f"Sorry, I encountered an error: {user_friendly_error}",
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "agent_type": "system",
                                        "error": True
                                    },
                                    "investigation_id": investigation_id,
                                },
                                investigation_id,
                            )

                            await websocket.send_json({
                                "type": "error",
                                "message": user_friendly_error,
                            })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    })
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
            await ws_manager.disconnect(websocket, user_id)
        
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            await ws_manager.disconnect(websocket, user_id)
    
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Authentication failed"
        })
        await websocket.close()

