"""WebSocket service for real-time communication"""

import asyncio
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime
import json
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[Any]] = {}
        # Store connections by investigation_id for targeted updates
        self.investigation_rooms: Dict[str, Set[Any]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: Any, user_id: str):
        """Add a new WebSocket connection"""
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            logger.info(f"WebSocket connected for user {user_id}")

    async def disconnect(self, websocket: Any, user_id: str):
        """Remove a WebSocket connection"""
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from all investigation rooms
            for room_id, connections in list(self.investigation_rooms.items()):
                connections.discard(websocket)
                if not connections:
                    del self.investigation_rooms[room_id]
            
            logger.info(f"WebSocket disconnected for user {user_id}")

    async def join_investigation(self, websocket: Any, investigation_id: str):
        """Add connection to an investigation room"""
        async with self._lock:
            if investigation_id not in self.investigation_rooms:
                self.investigation_rooms[investigation_id] = set()
            self.investigation_rooms[investigation_id].add(websocket)
            logger.info(f"WebSocket joined investigation room {investigation_id}")

    async def leave_investigation(self, websocket: Any, investigation_id: str):
        """Remove connection from an investigation room"""
        async with self._lock:
            if investigation_id in self.investigation_rooms:
                self.investigation_rooms[investigation_id].discard(websocket)
                if not self.investigation_rooms[investigation_id]:
                    del self.investigation_rooms[investigation_id]
            logger.info(f"WebSocket left investigation room {investigation_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                await self.disconnect(connection, user_id)

    async def broadcast_to_investigation(self, message: dict, investigation_id: str):
        """Send message to all users in an investigation room"""
        if investigation_id in self.investigation_rooms:
            disconnected = set()
            for connection in self.investigation_rooms[investigation_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to investigation {investigation_id}: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            async with self._lock:
                for connection in disconnected:
                    self.investigation_rooms[investigation_id].discard(connection)

    async def broadcast_to_all(self, message: dict):
        """Send message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    async def send_event(
        self,
        event_type: str,
        data: dict,
        user_id: Optional[str] = None,
        investigation_id: Optional[str] = None,
    ):
        """Send an event message"""
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if user_id:
            await self.send_personal_message(message, user_id)
        elif investigation_id:
            await self.broadcast_to_investigation(message, investigation_id)
        else:
            await self.broadcast_to_all(message)

    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        user_id: Optional[str] = None,
    ):
        """Send a notification"""
        notification_message = {
            "type": "notification",
            "data": {
                "title": title,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        if user_id:
            await self.send_personal_message(notification_message, user_id)
        else:
            await self.broadcast_to_all(notification_message)

    async def send_agent_update(
        self,
        agent_type: str,
        status: str,
        current_task: Optional[str] = None,
        progress: Optional[float] = None,
        investigation_id: Optional[str] = None,
    ):
        """Send an agent status update"""
        message = {
            "type": "agent_update",
            "data": {
                "agent_type": agent_type,
                "status": status,
                "current_task": current_task,
                "progress": progress,
                "last_update": datetime.utcnow().isoformat(),
            },
        }

        if investigation_id:
            await self.broadcast_to_investigation(message, investigation_id)
        else:
            await self.broadcast_to_all(message)

    async def send_investigation_update(
        self,
        investigation_id: str,
        update_type: str,
        data: dict,
    ):
        """Send an investigation update"""
        message = {
            "type": "investigation_update",
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast_to_investigation(message, investigation_id)


# Global WebSocket manager instance
_ws_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create the WebSocket manager instance"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager

