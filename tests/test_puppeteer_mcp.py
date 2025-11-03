"""Tests for Puppeteer MCP server"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import base64

# Check if playwright is available
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Skip all tests if playwright is not available
pytestmark = pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="playwright not installed")

if HAS_PLAYWRIGHT:
    from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer


class TestPuppeteerMCPServer:
    """Tests for PuppeteerMCPServer"""
    
    def test_puppeteer_server_initialization(self):
        """Test PuppeteerMCPServer initialization"""
        server = PuppeteerMCPServer(headless=True, timeout=30000)
        
        assert server.name == "puppeteer"
        assert server.headless is True
        assert server.timeout == 30000
        assert server._initialized is False
        assert len(server.tools) == 8  # All registered tools
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list_tools method"""
        server = PuppeteerMCPServer()
        
        tools = await server.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 8
        
        tool_names = [tool["name"] for tool in tools]
        assert "puppeteer_navigate" in tool_names
        assert "puppeteer_screenshot" in tool_names
        assert "puppeteer_click" in tool_names
        assert "puppeteer_fill" in tool_names
        assert "puppeteer_evaluate" in tool_names
        assert "puppeteer_get_content" in tool_names
        assert "puppeteer_wait_for_selector" in tool_names
        assert "puppeteer_close" in tool_names
    
    @pytest.mark.asyncio
    async def test_navigate_tool(self):
        """Test puppeteer_navigate tool"""
        server = PuppeteerMCPServer()
        
        # Mock browser components
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            mock_response = Mock()
            mock_response.status = 200
            
            mock_page.goto = AsyncMock(return_value=mock_response)
            mock_page.title = AsyncMock(return_value="Test Page")
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            # Call navigate
            result = await server.call_tool(
                "puppeteer_navigate",
                {"url": "https://example.com", "wait_until": "load"}
            )
            
            assert result["success"] is True
            assert result["url"] == "https://example.com"
            assert result["status"] == 200
            assert result["title"] == "Test Page"
    
    @pytest.mark.asyncio
    async def test_screenshot_tool(self):
        """Test puppeteer_screenshot tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            # Mock screenshot response
            screenshot_data = b"fake_screenshot_data"
            mock_page.screenshot = AsyncMock(return_value=screenshot_data)
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            # Call screenshot
            result = await server.call_tool(
                "puppeteer_screenshot",
                {"full_page": True}
            )
            
            assert result["success"] is True
            assert "screenshot" in result
            assert result["format"] == "png"
            # Verify base64 encoding
            decoded = base64.b64decode(result["screenshot"])
            assert decoded == screenshot_data
    
    @pytest.mark.asyncio
    async def test_screenshot_with_selector(self):
        """Test puppeteer_screenshot with element selector"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            mock_element = AsyncMock()
            
            screenshot_data = b"element_screenshot"
            mock_element.screenshot = AsyncMock(return_value=screenshot_data)
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_screenshot",
                {"selector": ".some-element", "full_page": False}
            )
            
            assert result["success"] is True
            assert result["selector"] == ".some-element"
    
    @pytest.mark.asyncio
    async def test_click_tool(self):
        """Test puppeteer_click tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.click = AsyncMock()
            mock_page.wait_for_selector = AsyncMock()
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_click",
                {"selector": "#submit-button", "wait_for_selector": True}
            )
            
            assert result["success"] is True
            assert result["selector"] == "#submit-button"
            mock_page.wait_for_selector.assert_called_once()
            mock_page.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fill_tool(self):
        """Test puppeteer_fill tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.fill = AsyncMock()
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_fill",
                {"selector": "#username", "value": "test_user"}
            )
            
            assert result["success"] is True
            assert result["selector"] == "#username"
            assert result["value"] == "test_user"
            mock_page.fill.assert_called_once_with("#username", "test_user")
    
    @pytest.mark.asyncio
    async def test_evaluate_tool(self):
        """Test puppeteer_evaluate tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.evaluate = AsyncMock(return_value={"data": "result"})
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_evaluate",
                {"script": "return document.title;"}
            )
            
            assert result["success"] is True
            assert result["result"] == {"data": "result"}
    
    @pytest.mark.asyncio
    async def test_get_content_tool(self):
        """Test puppeteer_get_content tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_get_content",
                {}
            )
            
            assert result["success"] is True
            assert "<html>" in result["content"]
    
    @pytest.mark.asyncio
    async def test_wait_for_selector_tool(self):
        """Test puppeteer_wait_for_selector tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.wait_for_selector = AsyncMock()
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_wait_for_selector",
                {"selector": ".loading-complete", "timeout": 5000}
            )
            
            assert result["success"] is True
            assert result["found"] is True
            assert result["selector"] == ".loading-complete"
    
    @pytest.mark.asyncio
    async def test_close_tool(self):
        """Test puppeteer_close tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.close = AsyncMock()
            mock_page.set_default_timeout = Mock()
            mock_context.close = AsyncMock()
            mock_browser.close = AsyncMock()
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.stop = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            # Initialize first
            await server._ensure_initialized()
            
            # Then close
            result = await server.call_tool("puppeteer_close", {})
            
            assert result["success"] is True
            assert "message" in result
            assert server._initialized is False
    
    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self):
        """Test calling a nonexistent tool"""
        server = PuppeteerMCPServer()
        
        result = await server.call_tool("nonexistent_tool", {})
        
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test list_resources method"""
        server = PuppeteerMCPServer()
        
        resources = await server.list_resources()
        
        assert resources == []
    
    @pytest.mark.asyncio
    async def test_error_handling_navigate(self):
        """Test error handling in navigate tool"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(side_effect=Exception("Browser launch failed"))
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_navigate",
                {"url": "https://example.com"}
            )
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_screenshot_element_not_found(self):
        """Test screenshot when element is not found"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            # Element not found
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.set_default_timeout = Mock()
            
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            result = await server.call_tool(
                "puppeteer_screenshot",
                {"selector": ".nonexistent"}
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup method"""
        server = PuppeteerMCPServer()
        
        with patch('backend.mcp_servers.puppeteer_server.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.close = AsyncMock()
            mock_page.set_default_timeout = Mock()
            mock_context.close = AsyncMock()
            mock_browser.close = AsyncMock()
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.stop = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_playwright.return_value = mock_pw_instance
            
            # Initialize
            await server._ensure_initialized()
            assert server._initialized is True
            
            # Cleanup
            await server.cleanup()
            
            assert server._initialized is False
            assert server.page is None
            assert server.context is None
            assert server.browser is None

