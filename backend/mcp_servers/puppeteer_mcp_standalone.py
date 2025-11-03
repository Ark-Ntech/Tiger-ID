"""Standalone MCP server for Puppeteer using FastMCP"""

import sys
import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from typing import AsyncIterator

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP
from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer
from backend.config.settings import get_settings

# Initialize the puppeteer server instance
# We'll initialize it lazily to avoid initialization issues at import time
_puppeteer_server: Optional[PuppeteerMCPServer] = None


def get_puppeteer_server() -> PuppeteerMCPServer:
    """Get or create the puppeteer server instance"""
    global _puppeteer_server
    if _puppeteer_server is None:
        settings = get_settings()
        _puppeteer_server = PuppeteerMCPServer(
            headless=settings.puppeteer.headless,
            timeout=settings.puppeteer.timeout,
            viewport_width=settings.puppeteer.viewport_width,
            viewport_height=settings.puppeteer.viewport_height,
            user_agent=settings.puppeteer.user_agent
        )
    return _puppeteer_server


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Lifecycle management for the MCP server."""
    # Startup - puppeteer server will be initialized lazily on first tool call
    yield
    # Cleanup on shutdown
    global _puppeteer_server
    if _puppeteer_server is not None:
        await _puppeteer_server.cleanup()
        _puppeteer_server = None


# Create FastMCP instance with lifespan
mcp = FastMCP("Puppeteer Browser Automation", lifespan=lifespan)


# Register tools from PuppeteerMCPServer as FastMCP tools
@mcp.tool()
async def puppeteer_navigate(url: str, wait_until: str = "load") -> dict:
    """Navigate to a URL in the browser.
    
    Args:
        url: URL to navigate to
        wait_until: When to consider navigation succeeded (load, domcontentloaded, networkidle)
    
    Returns:
        Dictionary with url, status, title, and success status
    """
    server = get_puppeteer_server()
    return await server._handle_navigate(url, wait_until)


@mcp.tool()
async def puppeteer_screenshot(selector: Optional[str] = None, full_page: bool = True) -> dict:
    """Take a screenshot of the current page or a specific element.
    
    Args:
        selector: CSS selector for element to screenshot (optional, full page if not provided)
        full_page: Capture full scrollable page (default: True)
    
    Returns:
        Dictionary with screenshot (base64 encoded), format, selector, and success status
    """
    server = get_puppeteer_server()
    return await server._handle_screenshot(selector, full_page)


@mcp.tool()
async def puppeteer_click(selector: str, wait_for_selector: bool = True) -> dict:
    """Click on an element identified by CSS selector.
    
    Args:
        selector: CSS selector for element to click
        wait_for_selector: Wait for selector to be visible before clicking (default: True)
    
    Returns:
        Dictionary with selector and success status
    """
    server = get_puppeteer_server()
    return await server._handle_click(selector, wait_for_selector)


@mcp.tool()
async def puppeteer_fill(selector: str, value: str) -> dict:
    """Fill an input field with text.
    
    Args:
        selector: CSS selector for input element
        value: Value to fill into the input
    
    Returns:
        Dictionary with selector, value, and success status
    """
    server = get_puppeteer_server()
    return await server._handle_fill(selector, value)


@mcp.tool()
async def puppeteer_evaluate(script: str) -> dict:
    """Execute JavaScript code in the browser context.
    
    Args:
        script: JavaScript code to execute
    
    Returns:
        Dictionary with result and success status
    """
    server = get_puppeteer_server()
    return await server._handle_evaluate(script)


@mcp.tool()
async def puppeteer_get_content(selector: Optional[str] = None) -> dict:
    """Get the HTML content of the current page or specific element.
    
    Args:
        selector: CSS selector for specific element (optional, full page if not provided)
    
    Returns:
        Dictionary with content, selector, and success status
    """
    server = get_puppeteer_server()
    return await server._handle_get_content(selector)


@mcp.tool()
async def puppeteer_wait_for_selector(selector: str, timeout: int = 30000) -> dict:
    """Wait for an element to appear on the page.
    
    Args:
        selector: CSS selector to wait for
        timeout: Timeout in milliseconds (default: 30000)
    
    Returns:
        Dictionary with selector, found status, and success status
    """
    server = get_puppeteer_server()
    return await server._handle_wait_for_selector(selector, timeout)


@mcp.tool()
async def puppeteer_close() -> dict:
    """Close the browser and clean up resources.
    
    Returns:
        Dictionary with success status and message
    """
    server = get_puppeteer_server()
    return await server._handle_close()


if __name__ == "__main__":
    mcp.run()

