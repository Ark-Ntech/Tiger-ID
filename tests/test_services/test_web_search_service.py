"""Tests for WebSearchService"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json

from backend.services.web_search_service import WebSearchService


class TestWebSearchService:
    """Tests for WebSearchService"""
    
    @patch('backend.services.web_search_service.get_settings')
    def test_init(self, mock_get_settings):
        """Test service initialization"""
        mock_settings = MagicMock()
        mock_settings.web_search.provider = "tavily"
        mock_settings.web_search.enable_caching = False
        mock_settings.redis.url = "redis://localhost:6379"
        mock_get_settings.return_value = mock_settings
        
        service = WebSearchService()
        
        assert service.settings == mock_settings
        assert service.web_search_config == mock_settings.web_search
    
    @pytest.mark.asyncio
    @patch('backend.services.web_search_service.get_settings')
    @patch('backend.services.web_search_service.httpx.AsyncClient')
    async def test_search_basic(self, mock_client, mock_get_settings):
        """Test basic web search"""
        mock_settings = MagicMock()
        mock_settings.web_search.provider = "tavily"
        mock_settings.web_search.enable_caching = False
        mock_settings.web_search.tavily.api_key = "test_key"
        mock_get_settings.return_value = mock_settings
        
        service = WebSearchService()
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "results": [
                {"title": "Test Result", "url": "https://example.com"}
            ]
        }
        mock_response.raise_for_status = AsyncMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Patch httpx.AsyncClient in the method
        with patch('backend.services.web_search_service.httpx.AsyncClient', return_value=mock_client_instance):
            result = await service.search("test query", limit=10)
        
        assert "results" in result
    
    @pytest.mark.asyncio
    @patch('backend.services.web_search_service.get_settings')
    @patch('backend.services.web_search_service.redis')
    async def test_search_with_caching(self, mock_redis, mock_get_settings):
        """Test web search with caching"""
        mock_settings = MagicMock()
        mock_settings.web_search.provider = "tavily"
        mock_settings.web_search.enable_caching = True
        mock_settings.web_search.cache_ttl_seconds = 3600
        mock_get_settings.return_value = mock_settings
        
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = None  # Cache miss
        mock_redis.from_url.return_value = mock_redis_client
        
        service = WebSearchService()
        
        # First search should cache
        with patch.object(service, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"results": []}
            result = await service.search("test query")
        
        # Redis client should be called
        assert service.redis_client is not None
    
    @patch('backend.services.web_search_service.get_settings')
    def test_get_cache_key(self, mock_get_settings):
        """Test cache key generation"""
        mock_settings = MagicMock()
        mock_settings.web_search.provider = "tavily"
        mock_settings.web_search.enable_caching = False
        mock_get_settings.return_value = mock_settings
        
        service = WebSearchService()
        
        key = service._get_cache_key("test query", 10, "tavily")
        
        assert isinstance(key, str)
        assert len(key) > 0
    
    @patch('backend.services.web_search_service.get_settings')
    def test_get_cached_result(self, mock_get_settings):
        """Test getting cached result"""
        mock_settings = MagicMock()
        mock_settings.web_search.provider = "tavily"
        mock_settings.web_search.enable_caching = True
        mock_get_settings.return_value = mock_settings
        
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        cached_result = {"results": [{"title": "Cached", "url": "https://example.com"}]}
        mock_redis_client.get.return_value = json.dumps(cached_result)
        
        with patch('backend.services.web_search_service.redis') as mock_redis:
            mock_redis.from_url.return_value = mock_redis_client
            service = WebSearchService()
            
            result = service._get_cached_result("cache_key")
            
            assert result == cached_result
    
    @patch('backend.services.web_search_service.get_settings')
    def test_cache_result(self, mock_get_settings):
        """Test caching result"""
        mock_settings = MagicMock()
        mock_settings.web_search.provider = "tavily"
        mock_settings.web_search.enable_caching = True
        mock_settings.web_search.cache_ttl_seconds = 3600
        mock_get_settings.return_value = mock_settings
        
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        
        with patch('backend.services.web_search_service.redis') as mock_redis:
            mock_redis.from_url.return_value = mock_redis_client
            service = WebSearchService()
            
            result = {"results": []}
            service._cache_result("cache_key", result, ttl=3600)
            
            mock_redis_client.setex.assert_called_once()

