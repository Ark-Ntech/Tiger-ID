"""Tests for CSRF middleware"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from backend.middleware.csrf_middleware import CSRFMiddleware


class TestCSRFMiddleware:
    """Tests for CSRFMiddleware"""
    
    @pytest.mark.asyncio
    async def test_generate_csrf_token(self):
        """Test CSRF token generation"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        token1 = middleware.generate_csrf_token()
        token2 = middleware.generate_csrf_token()
        
        assert token1 != token2  # Different tokens
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 in middleware.token_store
        assert token2 in middleware.token_store
    
    def test_validate_csrf_token_valid(self):
        """Test validating valid CSRF token"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        token = middleware.generate_csrf_token()
        result = middleware.validate_csrf_token(token)
        
        assert result is True
    
    def test_validate_csrf_token_invalid(self):
        """Test validating invalid CSRF token"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        result = middleware.validate_csrf_token("invalid_token")
        
        assert result is False
    
    def test_validate_csrf_token_empty(self):
        """Test validating empty CSRF token"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        result = middleware.validate_csrf_token("")
        
        assert result is False
    
    def test_validate_csrf_token_expired(self):
        """Test validating expired CSRF token"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app, token_lifetime=3600)
        
        token = middleware.generate_csrf_token()
        
        # Manually expire the token
        middleware.token_store[token] = datetime.utcnow() - timedelta(seconds=3601)
        
        result = middleware.validate_csrf_token(token)
        
        assert result is False
        assert token not in middleware.token_store  # Should be cleaned up
    
    @pytest.mark.asyncio
    async def test_safe_methods_skip_csrf(self):
        """Test that safe methods skip CSRF check"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v1/investigations"
        mock_request.headers.get.return_value = None

        from starlette.responses import Response
        mock_response = Response(content="test", status_code=200)
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        # Should have CSRF token in response headers
        assert "X-CSRF-Token" in result.headers
        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_skip_paths(self):
        """Test that skip paths skip CSRF check"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/auth/login"
        mock_request.headers.get.return_value = None
        
        mock_response = MagicMock()
        mock_call_next = AsyncMock(return_value=mock_response)
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_post_without_csrf_token(self):
        """Test POST request without CSRF token raises error"""
        from fastapi import HTTPException
        
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/investigations"
        mock_request.headers.get.return_value = None
        
        mock_call_next = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, mock_call_next)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_post_with_valid_csrf_token(self):
        """Test POST request with valid CSRF token"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        token = middleware.generate_csrf_token()
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/investigations"
        mock_request.headers.get.return_value = token
        mock_request.headers.get.side_effect = lambda key, default=None: token if key == "X-CSRF-Token" else default
        
        mock_response = MagicMock()
        mock_call_next = AsyncMock(return_value=mock_response)
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_post_with_invalid_csrf_token(self):
        """Test POST request with invalid CSRF token raises error"""
        from fastapi import HTTPException
        
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app)
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/investigations"
        mock_request.headers.get.return_value = "invalid_token"
        
        mock_call_next = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, mock_call_next)
        
        assert exc_info.value.status_code == 403
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens"""
        mock_app = MagicMock()
        middleware = CSRFMiddleware(mock_app, token_lifetime=3600)
        
        # Generate tokens
        token1 = middleware.generate_csrf_token()
        token2 = middleware.generate_csrf_token()
        
        # Manually expire one token
        middleware.token_store[token1] = datetime.utcnow() - timedelta(seconds=3601)
        
        # Cleanup
        middleware.cleanup_expired_tokens()
        
        assert token1 not in middleware.token_store
        assert token2 in middleware.token_store  # Not expired

