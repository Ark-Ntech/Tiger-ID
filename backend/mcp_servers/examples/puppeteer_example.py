"""Example usage of the Puppeteer MCP Server

This example demonstrates how to use the Puppeteer MCP server
to automate browser interactions.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer


async def basic_navigation_example():
    """Example: Navigate to a website and take a screenshot"""
    server = PuppeteerMCPServer(headless=True)
    
    try:
        # Navigate to a website
        print("Navigating to example.com...")
        nav_result = await server.call_tool(
            "puppeteer_navigate",
            {"url": "https://example.com", "wait_until": "load"}
        )
        print(f"Navigation result: {nav_result}")
        
        # Take a screenshot
        print("\nTaking screenshot...")
        screenshot_result = await server.call_tool(
            "puppeteer_screenshot",
            {"full_page": True}
        )
        if screenshot_result.get("success"):
            print("Screenshot captured successfully!")
            # The screenshot is base64 encoded in screenshot_result["screenshot"]
        
        # Get page content
        print("\nGetting page content...")
        content_result = await server.call_tool(
            "puppeteer_get_content",
            {}
        )
        if content_result.get("success"):
            print(f"Page content length: {len(content_result['content'])} characters")
        
    finally:
        # Always close the browser when done
        await server.cleanup()


async def form_interaction_example():
    """Example: Fill out a form and click submit"""
    server = PuppeteerMCPServer(headless=True)
    
    try:
        # Navigate to a page with a form
        await server.call_tool(
            "puppeteer_navigate",
            {"url": "https://example.com/login"}
        )
        
        # Fill in username
        await server.call_tool(
            "puppeteer_fill",
            {"selector": "#username", "value": "test_user"}
        )
        
        # Fill in password
        await server.call_tool(
            "puppeteer_fill",
            {"selector": "#password", "value": "test_password"}
        )
        
        # Click submit button
        await server.call_tool(
            "puppeteer_click",
            {"selector": "#submit-button", "wait_for_selector": True}
        )
        
        # Wait for success indicator
        wait_result = await server.call_tool(
            "puppeteer_wait_for_selector",
            {"selector": ".success-message", "timeout": 5000}
        )
        
        if wait_result.get("success"):
            print("Form submitted successfully!")
        
    finally:
        await server.cleanup()


async def javascript_execution_example():
    """Example: Execute JavaScript in the browser"""
    server = PuppeteerMCPServer(headless=True)
    
    try:
        # Navigate to a page
        await server.call_tool(
            "puppeteer_navigate",
            {"url": "https://example.com"}
        )
        
        # Execute JavaScript to get page information
        result = await server.call_tool(
            "puppeteer_evaluate",
            {
                "script": """() => {
                    return {
                        title: document.title,
                        url: window.location.href,
                        links: document.querySelectorAll('a').length
                    };
                }"""
            }
        )
        
        if result.get("success"):
            page_info = result.get("result")
            print(f"Page Title: {page_info.get('title')}")
            print(f"URL: {page_info.get('url')}")
            print(f"Number of links: {page_info.get('links')}")
        
    finally:
        await server.cleanup()


async def element_screenshot_example():
    """Example: Take screenshot of specific element"""
    server = PuppeteerMCPServer(headless=True)
    
    try:
        # Navigate to a page
        await server.call_tool(
            "puppeteer_navigate",
            {"url": "https://example.com"}
        )
        
        # Take screenshot of a specific element
        result = await server.call_tool(
            "puppeteer_screenshot",
            {"selector": "h1", "full_page": False}
        )
        
        if result.get("success"):
            print("Element screenshot captured!")
            # Save or process the base64 image data
            screenshot_data = result.get("screenshot")
            
    finally:
        await server.cleanup()


async def available_tools_example():
    """Example: List all available tools"""
    server = PuppeteerMCPServer()
    
    tools = await server.list_tools()
    
    print("Available Puppeteer Tools:")
    print("-" * 50)
    for tool in tools:
        print(f"\nTool: {tool['name']}")
        print(f"Description: {tool['description']}")
        print(f"Parameters: {tool['parameters'].get('properties', {}).keys()}")


if __name__ == "__main__":
    print("=" * 60)
    print("Puppeteer MCP Server Examples")
    print("=" * 60)
    
    # Run examples
    print("\n1. Available Tools:")
    asyncio.run(available_tools_example())
    
    print("\n\n2. Basic Navigation Example:")
    asyncio.run(basic_navigation_example())
    
    print("\n\n3. JavaScript Execution Example:")
    asyncio.run(javascript_execution_example())
    
    # Note: Form and element examples would require actual pages with forms
    # Uncomment these if you have test pages:
    # print("\n\n4. Form Interaction Example:")
    # asyncio.run(form_interaction_example())
    
    # print("\n\n5. Element Screenshot Example:")
    # asyncio.run(element_screenshot_example())

