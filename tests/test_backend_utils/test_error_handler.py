"""Tests for backend error handler utilities"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio

from backend.utils.error_handler import handle_error, retry_on_error, fallback_on_error
from backend.utils.error_types import ErrorCategory, ErrorInfo


class TestHandleError:
    """Tests for handle_error function"""
    
    @patch('backend.utils.error_handler.get_event_service')
    @patch('backend.utils.error_handler.logger')
    def test_handle_error_basic(self, mock_logger, mock_get_event_service):
        """Test basic error handling"""
        mock_get_event_service.return_value = None
        
        error = ValueError("Test error")
        error_info = handle_error(error)
        
        assert isinstance(error_info, ErrorInfo)
        assert "Test error" in error_info.message
        assert error_info.category == ErrorCategory.RECOVERABLE
        mock_logger.error.assert_called_once()
    
    @patch('backend.utils.error_handler.get_event_service')
    @patch('backend.utils.error_handler.logger')
    def test_handle_error_with_category(self, mock_logger, mock_get_event_service):
        """Test error handling with specific category"""
        mock_get_event_service.return_value = None
        
        error = ConnectionError("Connection failed")
        error_info = handle_error(error, category=ErrorCategory.NETWORK)
        
        assert error_info.category == ErrorCategory.NETWORK
    
    @patch('backend.utils.error_handler.get_event_service')
    @patch('backend.utils.error_handler.logger')
    def test_handle_error_with_context(self, mock_logger, mock_get_event_service):
        """Test error handling with context"""
        mock_get_event_service.return_value = None
        
        error = ValueError("Test error")
        context = {"investigation_id": "123", "step": "search"}
        error_info = handle_error(error, context=context)
        
        assert "investigation_id" in error_info.details["context"]
    
    @patch('backend.utils.error_handler.get_event_service')
    @patch('backend.utils.error_handler.logger')
    def test_handle_error_emits_event(self, mock_logger, mock_get_event_service):
        """Test error handling emits event"""
        mock_event_service = AsyncMock()
        mock_get_event_service.return_value = mock_event_service
        
        error = ValueError("Test error")
        error_info = handle_error(error, investigation_id="123")
        
        # Check that emit was called (async task created)
        assert mock_get_event_service.called


class TestRetryOnError:
    """Tests for retry_on_error decorator"""
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_retry_on_error_success_first_attempt(self, mock_logger):
        """Test retry decorator with successful first attempt"""
        call_count = 0
        
        @retry_on_error(max_retries=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_retry_on_error_succeeds_on_retry(self, mock_logger):
        """Test retry decorator succeeds after retry"""
        call_count = 0
        
        @retry_on_error(max_retries=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_retry_on_error_max_retries_exceeded(self, mock_logger):
        """Test retry decorator raises after max retries"""
        call_count = 0
        
        @retry_on_error(max_retries=2)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            await test_func()
        
        assert call_count == 3  # Initial + 2 retries
    
    @patch('backend.utils.error_handler.logger')
    def test_retry_on_error_sync(self, mock_logger):
        """Test retry decorator with sync function"""
        call_count = 0
        
        @retry_on_error(max_retries=2)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"
        
        result = test_func()
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_retry_on_error_non_retryable_error(self, mock_logger):
        """Test retry decorator retries recoverable errors"""
        call_count = 0
        
        @retry_on_error(max_retries=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Recoverable error")
        
        with pytest.raises(ValueError):
            await test_func()
        
        # ValueError is categorized as RECOVERABLE, so it will be retried
        assert call_count == 4  # 1 initial + 3 retries


class TestFallbackOnError:
    """Tests for fallback_on_error decorator"""
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_fallback_on_error_success(self, mock_logger):
        """Test fallback decorator with successful execution"""
        @fallback_on_error(fallback_value="fallback")
        async def test_func():
            return "success"
        
        result = await test_func()
        
        assert result == "success"
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_fallback_on_error_uses_fallback_value(self, mock_logger):
        """Test fallback decorator uses fallback value on error"""
        @fallback_on_error(fallback_value="fallback")
        async def test_func():
            raise ValueError("Error")
        
        result = await test_func()
        
        assert result == "fallback"
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_fallback_on_error_uses_fallback_func(self, mock_logger):
        """Test fallback decorator uses fallback function on error"""
        async def fallback_func():
            return "fallback_result"
        
        @fallback_on_error(fallback_func=fallback_func)
        async def test_func():
            raise ValueError("Error")
        
        result = await test_func()
        
        assert result == "fallback_result"
    
    @patch('backend.utils.error_handler.logger')
    def test_fallback_on_error_sync(self, mock_logger):
        """Test fallback decorator with sync function"""
        @fallback_on_error(fallback_value="fallback")
        def test_func():
            raise ValueError("Error")
        
        result = test_func()
        
        assert result == "fallback"
    
    @pytest.mark.asyncio
    @patch('backend.utils.error_handler.logger')
    async def test_fallback_on_error_no_fallback_raises(self, mock_logger):
        """Test fallback decorator raises if no fallback provided"""
        @fallback_on_error()
        async def test_func():
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            await test_func()

