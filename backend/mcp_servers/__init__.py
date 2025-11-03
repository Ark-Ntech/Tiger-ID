"""MCP server implementations"""

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
from backend.mcp_servers.database_server import DatabaseMCPServer
from backend.mcp_servers.tiger_id_server import TigerIDMCPServer
from backend.mcp_servers.youtube_server import YouTubeMCPServer
from backend.mcp_servers.meta_server import MetaMCPServer

# Puppeteer server is optional (requires playwright)
try:
    from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer
    HAS_PUPPETEER = True
except ImportError:
    PuppeteerMCPServer = None
    HAS_PUPPETEER = False

__all__ = [
    "MCPServerBase",
    "MCPTool",
    "FirecrawlMCPServer",
    "DatabaseMCPServer",
    "TigerIDMCPServer",
    "YouTubeMCPServer",
    "MetaMCPServer",
]

if HAS_PUPPETEER:
    __all__.append("PuppeteerMCPServer")
