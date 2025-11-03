"""Tests for audit middleware"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4

from backend.middleware.audit_middleware import AuditMiddleware
from backend.database.models import User


class TestAuditMiddleware:
    """Tests for AuditMiddleware"""
    
    @pytest.mark.asyncio
    async def test_skip_paths(self):
        """Test that skip paths are not logged"""
        middleware = AuditMiddleware(MagicMock())
        
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.method = "GET"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
        # Should not try to log for skip paths
    
    @pytest.mark.asyncio
    @patch('backend.middleware.audit_middleware.get_db_session')
    @patch('backend.middleware.audit_middleware.get_audit_service')
    async def test_log_successful_request(self, mock_get_audit, mock_get_db):
        """Test logging successful request"""
        middleware = AuditMiddleware(MagicMock())
        
        # Setup mocks
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        mock_audit_service = MagicMock()
        mock_get_audit.return_value = mock_audit_service
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/investigations"
        mock_request.method = "POST"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        mock_request.state.user = None
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
        # Verify audit service was called
        mock_audit_service.log_action.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.middleware.audit_middleware.get_db_session')
    @patch('backend.middleware.audit_middleware.get_audit_service')
    async def test_log_request_with_user(self, mock_get_audit, mock_get_db):
        """Test logging request with authenticated user"""
        middleware = AuditMiddleware(MagicMock())
        
        # Setup mocks
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        mock_audit_service = MagicMock()
        mock_get_audit.return_value = mock_audit_service
        
        mock_user = MagicMock()
        mock_user.user_id = uuid4()
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/investigations/123"
        mock_request.method = "GET"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        mock_request.state.user = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify user_id was passed to audit
        call_args = mock_audit_service.log_action.call_args
        assert call_args[1]["user_id"] == mock_user.user_id
    
    @pytest.mark.asyncio
    @patch('backend.middleware.audit_middleware.get_db_session')
    @patch('backend.middleware.audit_middleware.get_audit_service')
    async def test_log_error_response(self, mock_get_audit, mock_get_db):
        """Test logging error response"""
        middleware = AuditMiddleware(MagicMock())
        
        # Setup mocks
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        mock_audit_service = MagicMock()
        mock_get_audit.return_value = mock_audit_service
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/investigations"
        mock_request.method = "POST"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        mock_request.state.user = None
        
        mock_response = MagicMock()
        mock_response.status_code = 400  # Error status
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify error status was logged
        call_args = mock_audit_service.log_action.call_args
        assert call_args[1]["status"] == "failed"
    
    @pytest.mark.asyncio
    @patch('backend.middleware.audit_middleware.get_db_session')
    @patch('backend.middleware.audit_middleware.get_audit_service')
    @patch('backend.middleware.audit_middleware.logger')
    async def test_log_exception(self, mock_logger, mock_get_audit, mock_get_db):
        """Test logging exception"""
        middleware = AuditMiddleware(MagicMock())
        
        # Setup mocks
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        mock_audit_service = MagicMock()
        mock_get_audit.return_value = mock_audit_service
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/investigations"
        mock_request.method = "POST"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        mock_request.state.user = None
        
        mock_call_next = AsyncMock(side_effect=ValueError("Test error"))
        
        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify error was logged
        call_args = mock_audit_service.log_action.call_args
        assert call_args[1]["status"] == "error"

