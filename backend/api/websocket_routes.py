"""WebSocket routes for real-time communication"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
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
    ws_manager = get_websocket_manager()
    
    # Accept connection
    await websocket.accept()
    
    # Authenticate user
    try:
        # Simple token validation (you may want to use get_current_user_ws helper)
        if not token:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication required"
            })
            await websocket.close()
            return
        
        # For now, extract user_id from token (simplified)
        # In production, properly validate JWT token
        user_id = "user_" + token[:8]  # Simplified for demo
        
        # Register connection
        await ws_manager.connect(websocket, user_id)
        
        # Send connection success message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected successfully",
            "user_id": user_id,
        })
        
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
                    # Handle chat messages (to be implemented with agent integration)
                    investigation_id = message.get("investigation_id")
                    content = message.get("content")
                    if investigation_id and content:
                        await ws_manager.broadcast_to_investigation(
                            {
                                "type": "chat_message",
                                "user_id": user_id,
                                "content": content,
                                "investigation_id": investigation_id,
                            },
                            investigation_id,
                        )
                
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

