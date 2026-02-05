"""Tests for WebSocket routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, WebSocketDisconnect


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_connection_manager_init(self):
        """Test ConnectionManager initialization."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()

        assert manager.active_connections == {}
        assert manager.investigation_locks == {}

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting a WebSocket."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        ws = AsyncMock(spec=WebSocket)

        await manager.connect(ws, "inv_123", "user_456")

        ws.accept.assert_called_once()
        assert "inv_123" in manager.active_connections
        assert manager.active_connections["inv_123"]["user_456"] == ws

    @pytest.mark.asyncio
    async def test_connect_multiple_users(self):
        """Test connecting multiple users to same investigation."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1, "inv_123", "user_1")
        await manager.connect(ws2, "inv_123", "user_2")

        assert len(manager.active_connections["inv_123"]) == 2

    def test_disconnect(self):
        """Test disconnecting a WebSocket."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.active_connections = {
            "inv_123": {"user_456": MagicMock()}
        }

        manager.disconnect("inv_123", "user_456")

        assert "user_456" not in manager.active_connections.get("inv_123", {})

    def test_disconnect_cleans_empty_investigation(self):
        """Test disconnecting removes empty investigation entries."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.active_connections = {
            "inv_123": {"user_456": MagicMock()}
        }

        manager.disconnect("inv_123", "user_456")

        assert "inv_123" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting message to all connections."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        manager.active_connections = {
            "inv_123": {"user_1": ws1, "user_2": ws2}
        }

        await manager.broadcast("inv_123", {"type": "update", "data": "test"})

        ws1.send_json.assert_called_once_with({"type": "update", "data": "test"})
        ws2.send_json.assert_called_once_with({"type": "update", "data": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected(self):
        """Test broadcast handles disconnected WebSockets."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_json.side_effect = Exception("Connection closed")

        manager.active_connections = {
            "inv_123": {"user_1": ws1}
        }

        # Should not raise
        await manager.broadcast("inv_123", {"type": "update"})

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending personal message to specific user."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        ws = AsyncMock(spec=WebSocket)

        manager.active_connections = {
            "inv_123": {"user_456": ws}
        }

        await manager.send_personal_message("inv_123", "user_456", {"type": "private"})

        ws.send_json.assert_called_once_with({"type": "private"})

    def test_get_connections(self):
        """Test getting connections for investigation."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.active_connections = {
            "inv_123": {"user_1": MagicMock(), "user_2": MagicMock()}
        }

        result = manager.get_connections("inv_123")

        assert len(result) == 2
        assert "user_1" in result
        assert "user_2" in result

    def test_get_connections_empty(self):
        """Test getting connections for non-existent investigation."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()

        result = manager.get_connections("non_existent")

        assert result == {}


class TestInvestigationLocks:
    """Tests for investigation locking mechanism."""

    def test_acquire_lock(self):
        """Test acquiring investigation lock."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()

        result = manager.acquire_lock("inv_123", "user_456")

        assert result is True
        assert manager.investigation_locks["inv_123"] == "user_456"

    def test_acquire_lock_already_locked(self):
        """Test acquiring lock when already locked by another user."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.investigation_locks["inv_123"] = "user_1"

        result = manager.acquire_lock("inv_123", "user_2")

        assert result is False
        assert manager.investigation_locks["inv_123"] == "user_1"

    def test_acquire_lock_same_user(self):
        """Test acquiring lock by same user succeeds."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.investigation_locks["inv_123"] = "user_456"

        result = manager.acquire_lock("inv_123", "user_456")

        assert result is True

    def test_release_lock(self):
        """Test releasing investigation lock."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.investigation_locks["inv_123"] = "user_456"

        result = manager.release_lock("inv_123", "user_456")

        assert result is True
        assert "inv_123" not in manager.investigation_locks

    def test_release_lock_wrong_user(self):
        """Test releasing lock by wrong user fails."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.investigation_locks["inv_123"] = "user_1"

        result = manager.release_lock("inv_123", "user_2")

        assert result is False
        assert manager.investigation_locks["inv_123"] == "user_1"

    def test_is_locked(self):
        """Test checking if investigation is locked."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.investigation_locks["inv_123"] = "user_456"

        assert manager.is_locked("inv_123") is True
        assert manager.is_locked("inv_456") is False

    def test_get_lock_holder(self):
        """Test getting lock holder."""
        from backend.api.websocket_routes import ConnectionManager

        manager = ConnectionManager()
        manager.investigation_locks["inv_123"] = "user_456"

        assert manager.get_lock_holder("inv_123") == "user_456"
        assert manager.get_lock_holder("inv_456") is None


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_websocket_connect_auth(self):
        """Test WebSocket connection requires auth."""
        from backend.api.websocket_routes import websocket_endpoint

        ws = AsyncMock(spec=WebSocket)
        ws.receive_json = AsyncMock(return_value={"type": "auth", "token": "valid_token"})

        with patch('backend.api.websocket_routes.verify_token') as mock_verify:
            mock_verify.return_value = {"user_id": "123"}

            with patch('backend.api.websocket_routes.manager') as mock_manager:
                mock_manager.connect = AsyncMock()
                mock_manager.disconnect = MagicMock()
                mock_manager.broadcast = AsyncMock()

                ws.receive_json.side_effect = [
                    {"type": "auth", "token": "valid_token"},
                    WebSocketDisconnect()
                ]

                await websocket_endpoint(ws, "inv_123")

                mock_manager.connect.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_invalid_auth(self):
        """Test WebSocket rejects invalid auth."""
        from backend.api.websocket_routes import websocket_endpoint

        ws = AsyncMock(spec=WebSocket)
        ws.receive_json = AsyncMock(return_value={"type": "auth", "token": "invalid"})

        with patch('backend.api.websocket_routes.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")

            ws.receive_json.side_effect = [
                {"type": "auth", "token": "invalid"},
            ]

            await websocket_endpoint(ws, "inv_123")

            ws.close.assert_called()


class TestChatMessageHandling:
    """Tests for chat message handling."""

    @pytest.mark.asyncio
    async def test_handle_chat_message(self):
        """Test handling chat message."""
        from backend.api.websocket_routes import handle_chat_message

        with patch('backend.api.websocket_routes.manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()

            message = {
                "type": "chat",
                "content": "Hello",
                "user_id": "123",
                "username": "testuser"
            }

            await handle_chat_message("inv_123", message)

            mock_manager.broadcast.assert_called()

    @pytest.mark.asyncio
    async def test_handle_chat_message_empty(self):
        """Test handling empty chat message."""
        from backend.api.websocket_routes import handle_chat_message

        with patch('backend.api.websocket_routes.manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()

            message = {
                "type": "chat",
                "content": "",
                "user_id": "123"
            }

            await handle_chat_message("inv_123", message)

            # Empty messages should not be broadcast
            mock_manager.broadcast.assert_not_called()


class TestProgressUpdates:
    """Tests for progress update handling."""

    @pytest.mark.asyncio
    async def test_send_progress_update(self):
        """Test sending progress update."""
        from backend.api.websocket_routes import send_progress_update

        with patch('backend.api.websocket_routes.manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await send_progress_update(
                investigation_id="inv_123",
                phase="stripe_analysis",
                progress=0.5,
                message="Processing..."
            )

            mock_manager.broadcast.assert_called_once()
            call_args = mock_manager.broadcast.call_args
            assert call_args[0][0] == "inv_123"
            assert call_args[0][1]["type"] == "progress"
            assert call_args[0][1]["phase"] == "stripe_analysis"
            assert call_args[0][1]["progress"] == 0.5

    @pytest.mark.asyncio
    async def test_send_error_update(self):
        """Test sending error update."""
        from backend.api.websocket_routes import send_error_update

        with patch('backend.api.websocket_routes.manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await send_error_update(
                investigation_id="inv_123",
                error="Something went wrong",
                phase="detection"
            )

            mock_manager.broadcast.assert_called_once()
            call_args = mock_manager.broadcast.call_args
            assert call_args[0][1]["type"] == "error"
            assert "Something went wrong" in call_args[0][1]["error"]


class TestTypingIndicators:
    """Tests for typing indicators."""

    @pytest.mark.asyncio
    async def test_handle_typing_start(self):
        """Test handling typing start."""
        from backend.api.websocket_routes import handle_typing_indicator

        with patch('backend.api.websocket_routes.manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await handle_typing_indicator("inv_123", "user_456", True)

            mock_manager.broadcast.assert_called()
            call_args = mock_manager.broadcast.call_args
            assert call_args[0][1]["type"] == "typing"
            assert call_args[0][1]["user_id"] == "user_456"
            assert call_args[0][1]["is_typing"] is True

    @pytest.mark.asyncio
    async def test_handle_typing_stop(self):
        """Test handling typing stop."""
        from backend.api.websocket_routes import handle_typing_indicator

        with patch('backend.api.websocket_routes.manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await handle_typing_indicator("inv_123", "user_456", False)

            call_args = mock_manager.broadcast.call_args
            assert call_args[0][1]["is_typing"] is False
