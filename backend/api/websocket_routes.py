"""WebSocket routes for real-time communication"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
from datetime import datetime
from backend.auth.auth import get_current_user_ws
from backend.services.websocket_service import get_websocket_manager
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


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
                    # Handle chat messages with OmniVinci and orchestrator integration
                    investigation_id = message.get("investigation_id")
                    content = message.get("content")
                    selected_tools = message.get("selected_tools", [])
                    
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
                                    selected_tools=selected_tools if selected_tools else None
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
                            logger.error(f"Error processing chat message ({error_type}): {error_msg}", exc_info=True)
                            
                            # Provide more specific error message
                            if "OmniVinci" in error_msg or "omnivinci" in error_msg.lower():
                                detailed_error = f"OmniVinci error: {error_msg}"
                            elif "Modal" in error_msg or "modal" in error_msg.lower():
                                detailed_error = f"Modal service error: {error_msg}. Check Modal configuration and connectivity."
                            elif "authentication" in error_msg.lower() or "auth" in error_msg.lower():
                                detailed_error = f"Authentication error: {error_msg}. Please check your credentials."
                            elif "timeout" in error_msg.lower():
                                detailed_error = f"Request timeout: {error_msg}. The operation took too long."
                            else:
                                detailed_error = f"Error ({error_type}): {error_msg}"
                            
                            # Send error message to chat
                            await ws_manager.broadcast_to_investigation(
                                {
                                    "type": "chat_message",
                                    "data": {
                                        "id": str(UUID(int=0)),
                                        "role": "assistant",
                                        "content": f"Sorry, I encountered an error: {detailed_error}",
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
                                "message": detailed_error,
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

