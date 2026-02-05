# Puppeteer MCP Server Documentation

The Puppeteer MCP Server provides browser automation capabilities using Playwright, enabling the Tiger ID system to interact with web pages, capture screenshots, execute JavaScript, and automate web-based tasks.

## Overview

The Puppeteer MCP Server is implemented in `backend/mcp_servers/puppeteer_server.py` and follows the same MCP server pattern as other servers in the system (Firecrawl, YouTube, Meta, etc.).

## Installation

The Puppeteer MCP server requires Playwright to be installed:

```bash
pip install playwright>=1.40.0
playwright install chromium
```

The `playwright install chromium` command downloads the Chromium browser binaries needed for automation.

## Available Tools

The Puppeteer MCP server provides 8 browser automation tools:

### 1. `puppeteer_navigate`
Navigate to a URL in the browser.

**Parameters:**
- `url` (string, required): URL to navigate to
- `wait_until` (string, optional): When to consider navigation succeeded
  - Options: `"load"`, `"domcontentloaded"`, `"networkidle"`
  - Default: `"load"`

**Returns:**
```json
{
  "url": "https://example.com",
  "status": 200,
  "title": "Example Domain",
  "success": true
}
```

### 2. `puppeteer_screenshot`
Take a screenshot of the current page or a specific element.

**Parameters:**
- `selector` (string, optional): CSS selector for element to screenshot
- `full_page` (boolean, optional): Capture full scrollable page (default: true)

**Returns:**
```json
{
  "screenshot": "base64_encoded_png_data",
  "format": "png",
  "selector": ".some-element",
  "success": true
}
```

### 3. `puppeteer_click`
Click on an element identified by CSS selector.

**Parameters:**
- `selector` (string, required): CSS selector for element to click
- `wait_for_selector` (boolean, optional): Wait for selector to be visible before clicking (default: true)

**Returns:**
```json
{
  "selector": "#submit-button",
  "success": true
}
```

### 4. `puppeteer_fill`
Fill an input field with text.

**Parameters:**
- `selector` (string, required): CSS selector for input element
- `value` (string, required): Value to fill into the input

**Returns:**
```json
{
  "selector": "#username",
  "value": "test_user",
  "success": true
}
```

### 5. `puppeteer_evaluate`
Execute JavaScript code in the browser context.

**Parameters:**
- `script` (string, required): JavaScript code to execute

**Returns:**
```json
{
  "result": {"title": "Example", "links": 5},
  "success": true
}
```

### 6. `puppeteer_get_content`
Get the HTML content of the current page or specific element.

**Parameters:**
- `selector` (string, optional): CSS selector for specific element

**Returns:**
```json
{
  "content": "<html>...</html>",
  "selector": null,
  "success": true
}
```

### 7. `puppeteer_wait_for_selector`
Wait for an element to appear on the page.

**Parameters:**
- `selector` (string, required): CSS selector to wait for
- `timeout` (integer, optional): Timeout in milliseconds (default: 30000)

**Returns:**
```json
{
  "selector": ".loading-complete",
  "found": true,
  "success": true
}
```

### 8. `puppeteer_close`
Close the browser and clean up resources.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "message": "Browser closed successfully"
}
```

## Usage Examples

### Basic Usage in Python

```python
from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer

async def example():
    server = PuppeteerMCPServer(headless=True)
    
    try:
        # Navigate to a page
        await server.call_tool(
            "puppeteer_navigate",
            {"url": "https://example.com"}
        )
        
        # Take a screenshot
        result = await server.call_tool(
            "puppeteer_screenshot",
            {"full_page": True}
        )
        
        # Get page content
        content = await server.call_tool(
            "puppeteer_get_content",
            {}
        )
        
    finally:
        await server.cleanup()
```

### Integration with Investigation Agents

The Puppeteer MCP server is integrated into the investigation workflow and can be used by agents:

#### Using Puppeteer via Orchestrator

```python
from backend.agents.orchestrator import OrchestratorAgent

orchestrator = OrchestratorAgent(db=db_session)

# Navigate to a page
result = await orchestrator.use_mcp_tool(
    server_name="puppeteer",
    tool_name="puppeteer_navigate",
    arguments={"url": "https://example.com"}
)

# Take screenshot
screenshot = await orchestrator.use_mcp_tool(
    server_name="puppeteer",
    tool_name="puppeteer_screenshot",
    arguments={"full_page": True}
)
```

#### Using Puppeteer via Research Agent

The `ResearchAgent` includes a `capture_web_evidence` method that uses Puppeteer:

```python
from backend.agents.research_agent import ResearchAgent
from backend.agents.orchestrator import OrchestratorAgent

research_agent = ResearchAgent(db=db_session)
orchestrator = OrchestratorAgent(db=db_session)

# Capture web evidence (screenshot + content)
evidence = await research_agent.capture_web_evidence(
    url="https://facility-website.com",
    orchestrator=orchestrator,
    take_screenshot=True,
    extract_content=True
)
```

#### Use Cases

1. **Web Evidence Collection**: Navigate to websites and capture screenshots for evidence
2. **Social Media Monitoring**: Automate checking of social media profiles
3. **Facility Website Analysis**: Extract information from facility websites
4. **Form Automation**: Submit reports or requests automatically
5. **Data Extraction**: Scrape information from dynamic websites

Example workflow:

```python
# In an investigation workflow
async def investigate_facility_website(orchestrator, facility_url):
    """Collect evidence from a facility website"""
    # Navigate to facility website
    nav_result = await orchestrator.use_mcp_tool(
        server_name="puppeteer",
        tool_name="puppeteer_navigate",
        arguments={"url": facility_url, "wait_until": "networkidle"}
    )
    
    if nav_result.get("success"):
        # Capture screenshot
        screenshot = await orchestrator.use_mcp_tool(
            server_name="puppeteer",
            tool_name="puppeteer_screenshot",
            arguments={"full_page": True}
        )
        
        # Extract contact information
        contact_info = await orchestrator.use_mcp_tool(
            server_name="puppeteer",
            tool_name="puppeteer_evaluate",
            arguments={
                "script": """() => {
                    return {
                        phone: document.querySelector('.phone')?.textContent,
                        email: document.querySelector('.email')?.textContent,
                        address: document.querySelector('.address')?.textContent
                    }
                }"""
            }
        )
        
        return {
            "screenshot": screenshot.get("screenshot"),
            "contact_info": contact_info.get("result")
        }
```

## Configuration

### Environment Variables

The Puppeteer MCP server can be configured via environment variables in your `.env` file:

```bash
# Puppeteer Browser Automation (MCP Server)
# Setup: Requires playwright to be installed
# Install: pip install playwright && playwright install chromium
# Documentation: https://playwright.dev/python/
PUPPETEER_ENABLED=false
PUPPETEER_HEADLESS=true
PUPPETEER_TIMEOUT=30000
PUPPETEER_VIEWPORT_WIDTH=1280
PUPPETEER_VIEWPORT_HEIGHT=720
PUPPETEER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### Enabling Puppeteer

1. Install Playwright: `pip install playwright>=1.40.0`
2. Install browser binaries: `python -m playwright install chromium`
3. Set `PUPPETEER_ENABLED=true` in your `.env` file
4. Restart your application

### Headless Mode

By default, the browser runs in headless mode (no visible window). You can change this:

```python
# Headless mode (default)
server = PuppeteerMCPServer(headless=True)

# With visible browser (useful for debugging)
server = PuppeteerMCPServer(headless=False)
```

### Timeout Settings

Default timeout is 30 seconds (30000ms). You can customize:

```python
# Custom timeout (60 seconds)
server = PuppeteerMCPServer(timeout=60000)
```

### Browser Configuration

The browser is configured with:
- **Viewport**: 1280x720
- **User Agent**: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
- **Browser**: Chromium (via Playwright)

## Best Practices

### 1. Always Clean Up
Always call `cleanup()` or `puppeteer_close` when done:

```python
try:
    # Your automation code
    pass
finally:
    await server.cleanup()
```

### 2. Error Handling
Check for errors in responses:

```python
result = await server.call_tool("puppeteer_navigate", {"url": url})
if not result.get("success"):
    print(f"Error: {result.get('error')}")
```

### 3. Wait for Elements
Use `puppeteer_wait_for_selector` before interacting with dynamic content:

```python
# Wait for element to load
await server.call_tool(
    "puppeteer_wait_for_selector",
    {"selector": "#dynamic-content", "timeout": 10000}
)

# Then interact with it
await server.call_tool(
    "puppeteer_click",
    {"selector": "#dynamic-content button"}
)
```

### 4. Resource Management
The browser consumes system resources. Close it when not in use:

```python
# For long-running processes, close between sessions
await server.call_tool("puppeteer_close", {})
```

## Testing

Comprehensive tests are available in `tests/test_puppeteer_mcp.py`:

```bash
python -m pytest tests/test_puppeteer_mcp.py -v
```

All tests use mocks to avoid requiring actual browser instances during testing.

## Troubleshooting

### Browser Not Found
If you get "Browser not found" errors:

```bash
playwright install chromium
```

### Timeout Errors
Increase timeout for slow-loading pages:

```python
await server.call_tool(
    "puppeteer_wait_for_selector",
    {"selector": ".slow-element", "timeout": 60000}
)
```

### Element Not Found
Ensure page is fully loaded before interacting:

```python
await server.call_tool(
    "puppeteer_navigate",
    {"url": url, "wait_until": "networkidle"}
)
```

## Rate Limiting Integration

The Tiger ID discovery system integrates Playwright with the `RateLimiter` class for responsible crawling:

### Per-Domain Rate Limiting

```python
from backend.services.facility_crawler_service import RateLimiter

rate_limiter = RateLimiter(
    requests_per_second=0.5,  # 2 seconds between requests
    max_backoff=60.0          # Maximum wait of 60 seconds
)

# Wait before making request
await rate_limiter.wait_for_slot(url)

# Report success/failure for backoff adjustment
rate_limiter.report_success(url)
rate_limiter.report_error(url, status_code=429)
```

### Exponential Backoff

The rate limiter automatically adjusts wait times based on server responses:

| HTTP Status | Backoff Behavior |
|-------------|------------------|
| 200 (success) | Reduce backoff by 0.9x (gradual recovery) |
| 429 (rate limited) | Double backoff (exponential increase) |
| 503 (service unavailable) | Double backoff |
| 520-524 (Cloudflare errors) | Double backoff |
| 5xx (server errors) | Increase backoff by 1.5x |

### Best Practices for Crawling

1. **Respect robots.txt**: Check robots.txt before crawling
2. **Use delays between pages**: Always wait between gallery page visits
3. **Monitor backoff stats**: Check `rate_limiter.get_stats()` for domains with high backoff
4. **Handle timeouts gracefully**: Don't hammer servers after timeouts

### Example: Rate-Limited Gallery Crawl

```python
async def crawl_facility_gallery(facility_url, rate_limiter):
    """Crawl gallery pages with rate limiting."""
    gallery_links = find_gallery_links(facility_url)

    for gallery_url in gallery_links[:5]:  # Limit to 5 pages
        await rate_limiter.wait_for_slot(gallery_url)

        try:
            async with page.goto(gallery_url, wait_until="networkidle"):
                images = await extract_images(page)
                rate_limiter.report_success(gallery_url)
        except TimeoutError:
            rate_limiter.report_error(gallery_url, 408)
```

## Security Considerations

1. **URL Validation**: Always validate URLs before navigation
2. **Credential Handling**: Never hardcode credentials; use secure storage
3. **Content Sanitization**: Sanitize any extracted content before storage
4. **Network Security**: Be aware of the websites you're automating
5. **Rate Limiting**: The discovery system includes built-in per-domain rate limiting

## Performance Tips

1. **Reuse Browser Instance**: Don't create new instances for every action
2. **Use Headless Mode**: Headless mode is faster and uses less resources
3. **Selective Screenshots**: Only capture screenshots when needed
4. **Cleanup Regularly**: Close browsers to free resources

## Integration Points

The Puppeteer MCP server integrates with:

- **Investigation Agents** (`backend/agents/`): For automated web research
- **Research Agent** (`backend/agents/research_agent.py`): For evidence collection
- **Export Service** (`backend/services/export_service.py`): For report generation
- **External API Service** (`backend/services/external_api_service.py`): For web-based API interactions

## Future Enhancements

Potential improvements:

1. Browser session persistence across calls
2. Cookie and local storage management
3. Network request interception
4. PDF generation from web pages
5. Mobile device emulation
6. Proxy support
7. Multiple browser contexts

## License

Same license as the Tiger ID project.

