"""Tests for YouTube and Meta MCP servers"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.mcp_servers.youtube_server import YouTubeMCPServer
from backend.mcp_servers.meta_server import MetaMCPServer


class TestYouTubeMCPServer:
    """Tests for YouTubeMCPServer"""
    
    @pytest.fixture
    def youtube_server(self):
        """Create YouTube MCP server instance"""
        with patch('backend.mcp_servers.youtube_server.get_api_clients') as mock_clients:
            mock_clients.return_value = {"youtube": None}
            server = YouTubeMCPServer(api_key="test_key")
            return server
    
    @pytest.mark.asyncio
    async def test_list_tools(self, youtube_server):
        """Test list tools"""
        tools = await youtube_server.list_tools()
        
        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "youtube_search_videos" in tool_names
        assert "youtube_get_channel" in tool_names
        assert "youtube_get_channel_videos" in tool_names
    
    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, youtube_server):
        """Test calling non-existent tool"""
        result = await youtube_server.call_tool("nonexistent_tool", {})
        
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_call_tool_no_client(self, youtube_server):
        """Test calling tool when client not initialized"""
        youtube_server.client = None
        
        result = await youtube_server.call_tool("youtube_search_videos", {"query": "test"})
        
        assert "error" in result
        assert "not initialized" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_search_videos_tool(self, youtube_server):
        """Test youtube_search_videos tool"""
        mock_client = Mock()
        mock_client.search_videos = AsyncMock(return_value=[
            {"video_id": "test_id", "title": "Test Video"}
        ])
        youtube_server.client = mock_client
        
        result = await youtube_server.call_tool(
            "youtube_search_videos",
            {"query": "test query", "max_results": 10}
        )
        
        assert "videos" in result
        assert len(result["videos"]) == 1
        assert result["videos"][0]["video_id"] == "test_id"
    
    @pytest.mark.asyncio
    async def test_get_channel_tool(self, youtube_server):
        """Test youtube_get_channel tool"""
        mock_client = Mock()
        mock_client.get_channel_info = AsyncMock(return_value={
            "channel_id": "test_channel",
            "title": "Test Channel",
            "subscriber_count": 1000
        })
        youtube_server.client = mock_client
        
        result = await youtube_server.call_tool(
            "youtube_get_channel",
            {"channel_id": "test_channel"}
        )
        
        assert "channel" in result
        assert result["channel"]["channel_id"] == "test_channel"
    
    @pytest.mark.asyncio
    async def test_list_resources(self, youtube_server):
        """Test list resources"""
        resources = await youtube_server.list_resources()
        
        assert isinstance(resources, list)
        assert len(resources) == 0


class TestMetaMCPServer:
    """Tests for MetaMCPServer"""
    
    @pytest.fixture
    def meta_server(self):
        """Create Meta MCP server instance"""
        with patch('backend.mcp_servers.meta_server.get_api_clients') as mock_clients:
            mock_clients.return_value = {"meta": None}
            server = MetaMCPServer(access_token="test_token")
            return server
    
    @pytest.mark.asyncio
    async def test_list_tools(self, meta_server):
        """Test list tools"""
        tools = await meta_server.list_tools()
        
        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "meta_get_page" in tool_names
        assert "meta_search_pages" in tool_names
        assert "meta_get_page_posts" in tool_names
    
    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, meta_server):
        """Test calling non-existent tool"""
        result = await meta_server.call_tool("nonexistent_tool", {})
        
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_call_tool_no_client(self, meta_server):
        """Test calling tool when client not initialized"""
        meta_server.client = None
        
        result = await meta_server.call_tool("meta_search_pages", {"query": "test"})
        
        assert "error" in result
        assert "not initialized" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_search_pages_tool(self, meta_server):
        """Test meta_search_pages tool"""
        mock_client = Mock()
        mock_client.search_pages = AsyncMock(return_value=[
            {"page_id": "test_page", "name": "Test Page"}
        ])
        meta_server.client = mock_client
        
        result = await meta_server.call_tool(
            "meta_search_pages",
            {"query": "test query", "limit": 10}
        )
        
        assert "pages" in result
        assert len(result["pages"]) == 1
        assert result["pages"][0]["page_id"] == "test_page"
    
    @pytest.mark.asyncio
    async def test_get_page_tool(self, meta_server):
        """Test meta_get_page tool"""
        mock_client = Mock()
        mock_client.get_page_info = AsyncMock(return_value={
            "page_id": "test_page",
            "name": "Test Page",
            "fan_count": 1000
        })
        meta_server.client = mock_client
        
        result = await meta_server.call_tool(
            "meta_get_page",
            {"page_id": "test_page"}
        )
        
        assert "page" in result
        assert result["page"]["page_id"] == "test_page"
    
    @pytest.mark.asyncio
    async def test_list_resources(self, meta_server):
        """Test list resources"""
        resources = await meta_server.list_resources()
        
        assert isinstance(resources, list)
        assert len(resources) == 0

