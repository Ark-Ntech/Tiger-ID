"""MCP server implementations"""

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
from backend.mcp_servers.database_server import DatabaseMCPServer
from backend.mcp_servers.tiger_id_server import TigerIDMCPServer
from backend.mcp_servers.youtube_server import YouTubeMCPServer
from backend.mcp_servers.meta_server import MetaMCPServer

# New MCP servers for enhanced investigation workflow
from backend.mcp_servers.sequential_thinking_server import (
    SequentialThinkingMCPServer,
    get_sequential_thinking_server
)
from backend.mcp_servers.image_analysis_server import (
    ImageAnalysisMCPServer,
    get_image_analysis_server
)
from backend.mcp_servers.deep_research_server import (
    DeepResearchMCPServer,
    get_deep_research_server
)
from backend.mcp_servers.report_generation_server import (
    ReportGenerationMCPServer,
    get_report_generation_server
)
from backend.mcp_servers.subagent_coordinator_server import (
    SubagentCoordinatorMCPServer,
    get_subagent_coordinator_server
)

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
    # New servers
    "SequentialThinkingMCPServer",
    "get_sequential_thinking_server",
    "ImageAnalysisMCPServer",
    "get_image_analysis_server",
    "DeepResearchMCPServer",
    "get_deep_research_server",
    "ReportGenerationMCPServer",
    "get_report_generation_server",
    "SubagentCoordinatorMCPServer",
    "get_subagent_coordinator_server",
]

if HAS_PUPPETEER:
    __all__.append("PuppeteerMCPServer")
