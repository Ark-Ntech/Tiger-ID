"""Tests for Meta API client"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.services.external_apis.meta_client import MetaClient


class TestMetaClient:
    """Tests for MetaClient"""
    
    @pytest.fixture
    def meta_client(self):
        """Create Meta client instance"""
        return MetaClient(
            access_token="test_access_token",
            app_id="test_app_id",
            app_secret="test_app_secret"
        )
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, meta_client):
        """Test successful health check"""
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "12345"}
            
            result = await meta_client.health_check()
            
            assert result is True
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, meta_client):
        """Test health check failure"""
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("API error")
            
            result = await meta_client.health_check()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_page_info(self, meta_client):
        """Test get page info"""
        mock_response = {
            "id": "page_id",
            "name": "Test Page",
            "username": "testpage",
            "about": "Page description",
            "category": "Non-profit",
            "category_list": [{"name": "Category 1"}],
            "fan_count": 1000,
            "followers_count": 500,
            "likes": 800,
            "link": "https://facebook.com/testpage",
            "phone": "+1234567890",
            "website": "https://example.com",
            "location": {"city": "City", "state": "State"},
            "verification_status": "verified",
            "picture": {"data": {"url": "http://picture.url"}}
        }
        
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            page_info = await meta_client.get_page_info("test_page_id")
            
            assert page_info is not None
            assert page_info["page_id"] == "page_id"
            assert page_info["name"] == "Test Page"
            assert page_info["fan_count"] == 1000
    
    @pytest.mark.asyncio
    async def test_get_page_info_not_found(self, meta_client):
        """Test get page info when page not found"""
        mock_response = {"error": {"message": "Page not found", "code": 803}}
        
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            page_info = await meta_client.get_page_info("nonexistent_page")
            
            assert page_info is None
    
    @pytest.mark.asyncio
    async def test_search_pages(self, meta_client):
        """Test page search"""
        mock_response = {
            "data": [
                {
                    "id": "page_id_1",
                    "name": "Test Page 1",
                    "username": "testpage1",
                    "about": "Description",
                    "category": "Non-profit",
                    "fan_count": 1000,
                    "link": "https://facebook.com/testpage1",
                    "picture": {"data": {"url": "http://picture.url"}}
                }
            ]
        }
        
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            pages = await meta_client.search_pages("test query", limit=10)
            
            assert len(pages) == 1
            assert pages[0]["page_id"] == "page_id_1"
            assert pages[0]["name"] == "Test Page 1"
    
    @pytest.mark.asyncio
    async def test_get_page_posts(self, meta_client):
        """Test get page posts"""
        mock_response = {
            "data": [
                {
                    "id": "post_id",
                    "message": "Test post message",
                    "created_time": "2024-01-01T00:00:00+0000",
                    "updated_time": "2024-01-01T00:00:00+0000",
                    "shares": {"count": 10},
                    "likes": {"summary": {"total_count": 50}},
                    "comments": {"summary": {"total_count": 20}},
                    "permalink_url": "https://facebook.com/post"
                }
            ]
        }
        
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            posts = await meta_client.get_page_posts("page_id", limit=10)
            
            assert len(posts) == 1
            assert posts[0]["post_id"] == "post_id"
            assert posts[0]["message"] == "Test post message"
            assert posts[0]["like_count"] == 50
    
    @pytest.mark.asyncio
    async def test_get_post_details(self, meta_client):
        """Test get post details"""
        mock_response = {
            "id": "post_id",
            "message": "Post message",
            "created_time": "2024-01-01T00:00:00+0000",
            "updated_time": "2024-01-01T00:00:00+0000",
            "from": {"id": "user_id", "name": "User Name"},
            "shares": {"count": 5},
            "likes": {"summary": {"total_count": 30}},
            "comments": {"summary": {"total_count": 10}},
            "permalink_url": "https://facebook.com/post",
            "attachments": {"data": []}
        }
        
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            post_details = await meta_client.get_post_details("post_id")
            
            assert post_details is not None
            assert post_details["post_id"] == "post_id"
            assert post_details["message"] == "Post message"
            assert post_details["like_count"] == 30
    
    @pytest.mark.asyncio
    async def test_get_post_comments(self, meta_client):
        """Test get post comments"""
        mock_response = {
            "data": [
                {
                    "id": "comment_id",
                    "message": "Great post!",
                    "from": {"id": "user_id", "name": "User"},
                    "created_time": "2024-01-01T00:00:00+0000",
                    "like_count": 5,
                    "comment_count": 0
                }
            ]
        }
        
        with patch.object(meta_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            comments = await meta_client.get_post_comments("post_id", limit=10)
            
            assert len(comments) == 1
            assert comments[0]["comment_id"] == "comment_id"
            assert comments[0]["message"] == "Great post!"
    
    @pytest.mark.asyncio
    async def test_request_with_access_token(self, meta_client):
        """Test that access token is added as query parameter"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {"id": "12345"}
            mock_response.raise_for_status.return_value = None
            
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None
            mock_async_client.request = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            await meta_client._request("GET", "/me", params={})
            
            # Verify access_token parameter was added
            call_args = mock_async_client.request.call_args
            assert call_args is not None
            # Check that params include access_token
            assert "access_token" in (call_args[1] or {}).get("params", {})

