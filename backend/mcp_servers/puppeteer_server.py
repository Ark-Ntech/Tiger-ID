"""Puppeteer MCP server for browser automation using Playwright"""

from typing import Dict, Any, List, Optional
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.config.settings import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class PuppeteerMCPServer(MCPServerBase):
    """Puppeteer MCP server for browser automation"""
    
    def __init__(
        self,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        viewport_width: Optional[int] = None,
        viewport_height: Optional[int] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Puppeteer MCP server
        
        Args:
            headless: Run browser in headless mode (optional, uses settings if not provided)
            timeout: Default timeout in milliseconds (optional, uses settings if not provided)
            viewport_width: Browser viewport width (optional, uses settings if not provided)
            viewport_height: Browser viewport height (optional, uses settings if not provided)
            user_agent: Browser user agent (optional, uses settings if not provided)
        """
        super().__init__("puppeteer")
        
        # Get settings
        settings = get_settings()
        
        # Use provided values or fallback to settings
        self.headless = headless if headless is not None else settings.puppeteer.headless
        self.timeout = timeout if timeout is not None else settings.puppeteer.timeout
        self.viewport_width = viewport_width if viewport_width is not None else settings.puppeteer.viewport_width
        self.viewport_height = viewport_height if viewport_height is not None else settings.puppeteer.viewport_height
        self.user_agent = user_agent if user_agent is not None else settings.puppeteer.user_agent
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = False
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        self.tools = {
            "puppeteer_navigate": MCPTool(
                name="puppeteer_navigate",
                description="Navigate to a URL in the browser",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to navigate to"
                        },
                        "wait_until": {
                            "type": "string",
                            "description": "When to consider navigation succeeded",
                            "enum": ["load", "domcontentloaded", "networkidle"],
                            "default": "load"
                        }
                    },
                    "required": ["url"]
                },
                handler=self._handle_navigate
            ),
            "puppeteer_screenshot": MCPTool(
                name="puppeteer_screenshot",
                description="Take a screenshot of the current page or a specific element",
                parameters={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for element to screenshot (optional, full page if not provided)"
                        },
                        "full_page": {
                            "type": "boolean",
                            "description": "Capture full scrollable page",
                            "default": True
                        }
                    },
                    "required": []
                },
                handler=self._handle_screenshot
            ),
            "puppeteer_click": MCPTool(
                name="puppeteer_click",
                description="Click on an element identified by CSS selector",
                parameters={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for element to click"
                        },
                        "wait_for_selector": {
                            "type": "boolean",
                            "description": "Wait for selector to be visible before clicking",
                            "default": True
                        }
                    },
                    "required": ["selector"]
                },
                handler=self._handle_click
            ),
            "puppeteer_fill": MCPTool(
                name="puppeteer_fill",
                description="Fill an input field with text",
                parameters={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for input element"
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to fill into the input"
                        }
                    },
                    "required": ["selector", "value"]
                },
                handler=self._handle_fill
            ),
            "puppeteer_evaluate": MCPTool(
                name="puppeteer_evaluate",
                description="Execute JavaScript code in the browser context",
                parameters={
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "string",
                            "description": "JavaScript code to execute"
                        }
                    },
                    "required": ["script"]
                },
                handler=self._handle_evaluate
            ),
            "puppeteer_get_content": MCPTool(
                name="puppeteer_get_content",
                description="Get the HTML content of the current page",
                parameters={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for specific element (optional, full page if not provided)"
                        }
                    },
                    "required": []
                },
                handler=self._handle_get_content
            ),
            "puppeteer_wait_for_selector": MCPTool(
                name="puppeteer_wait_for_selector",
                description="Wait for an element to appear on the page",
                parameters={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to wait for"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in milliseconds",
                            "default": 30000
                        }
                    },
                    "required": ["selector"]
                },
                handler=self._handle_wait_for_selector
            ),
            "puppeteer_close": MCPTool(
                name="puppeteer_close",
                description="Close the browser and clean up resources",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                handler=self._handle_close
            )
        }
    
    async def _ensure_initialized(self):
        """Ensure browser is initialized"""
        if not self._initialized:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
                self.context = await self.browser.new_context(
                    viewport={"width": self.viewport_width, "height": self.viewport_height},
                    user_agent=self.user_agent
                )
                self.page = await self.context.new_page()
                self.page.set_default_timeout(self.timeout)
                self._initialized = True
                logger.info("Puppeteer browser initialized", headless=self.headless, viewport=f"{self.viewport_width}x{self.viewport_height}")
            except Exception as e:
                logger.error("Failed to initialize browser", error=str(e), exc_info=True)
                raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
        
        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e), exc_info=True)
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return []
    
    async def _handle_navigate(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """Handle page navigation"""
        try:
            await self._ensure_initialized()
            response = await self.page.goto(url, wait_until=wait_until)
            
            return {
                "url": url,
                "status": response.status if response else None,
                "title": await self.page.title(),
                "success": True
            }
        except Exception as e:
            logger.error("Navigation failed", url=url, error=str(e))
            return {"error": str(e), "url": url, "success": False}
    
    async def _handle_screenshot(self, selector: Optional[str] = None, full_page: bool = True) -> Dict[str, Any]:
        """Handle screenshot capture"""
        try:
            await self._ensure_initialized()
            
            screenshot_options = {
                "type": "png",
                "full_page": full_page if not selector else False
            }
            
            if selector:
                element = await self.page.query_selector(selector)
                if not element:
                    return {"error": f"Element not found: {selector}", "success": False}
                screenshot_bytes = await element.screenshot(**screenshot_options)
            else:
                screenshot_bytes = await self.page.screenshot(**screenshot_options)
            
            # Convert to base64 for transport
            import base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return {
                "screenshot": screenshot_base64,
                "format": "png",
                "selector": selector,
                "success": True
            }
        except Exception as e:
            logger.error("Screenshot failed", error=str(e))
            return {"error": str(e), "success": False}
    
    async def _handle_click(self, selector: str, wait_for_selector: bool = True) -> Dict[str, Any]:
        """Handle element click"""
        try:
            await self._ensure_initialized()
            
            if wait_for_selector:
                await self.page.wait_for_selector(selector, state="visible")
            
            await self.page.click(selector)
            
            return {
                "selector": selector,
                "success": True
            }
        except Exception as e:
            logger.error("Click failed", selector=selector, error=str(e))
            return {"error": str(e), "selector": selector, "success": False}
    
    async def _handle_fill(self, selector: str, value: str) -> Dict[str, Any]:
        """Handle input field fill"""
        try:
            await self._ensure_initialized()
            
            await self.page.fill(selector, value)
            
            return {
                "selector": selector,
                "value": value,
                "success": True
            }
        except Exception as e:
            logger.error("Fill failed", selector=selector, error=str(e))
            return {"error": str(e), "selector": selector, "success": False}
    
    async def _handle_evaluate(self, script: str) -> Dict[str, Any]:
        """Handle JavaScript evaluation"""
        try:
            await self._ensure_initialized()
            
            result = await self.page.evaluate(script)
            
            return {
                "result": result,
                "success": True
            }
        except Exception as e:
            logger.error("Evaluate failed", error=str(e))
            return {"error": str(e), "success": False}
    
    async def _handle_get_content(self, selector: Optional[str] = None) -> Dict[str, Any]:
        """Handle getting page/element content"""
        try:
            await self._ensure_initialized()
            
            if selector:
                element = await self.page.query_selector(selector)
                if not element:
                    return {"error": f"Element not found: {selector}", "success": False}
                content = await element.inner_html()
            else:
                content = await self.page.content()
            
            return {
                "content": content,
                "selector": selector,
                "success": True
            }
        except Exception as e:
            logger.error("Get content failed", error=str(e))
            return {"error": str(e), "success": False}
    
    async def _handle_wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Handle waiting for selector"""
        try:
            await self._ensure_initialized()
            
            await self.page.wait_for_selector(selector, timeout=timeout)
            
            return {
                "selector": selector,
                "found": True,
                "success": True
            }
        except Exception as e:
            logger.error("Wait for selector failed", selector=selector, error=str(e))
            return {"error": str(e), "selector": selector, "success": False}
    
    async def _handle_close(self) -> Dict[str, Any]:
        """Handle browser cleanup"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self._initialized = False
            logger.info("Puppeteer browser closed")
            
            return {"success": True, "message": "Browser closed successfully"}
        except Exception as e:
            logger.error("Close failed", error=str(e))
            return {"error": str(e), "success": False}
    
    async def cleanup(self):
        """Cleanup resources (called on server shutdown)"""
        await self._handle_close()

