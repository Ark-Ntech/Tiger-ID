"""MCP Tools API routes - separate router to avoid route conflicts"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.utils.logging import get_logger
from backend.mcp_servers import (
    FirecrawlMCPServer,
    DatabaseMCPServer,
    TigerIDMCPServer,
    YouTubeMCPServer,
    MetaMCPServer,
)
from backend.config.settings import get_settings

# Puppeteer is optional
try:
    from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer
    HAS_PUPPETEER = True
except ImportError:
    PuppeteerMCPServer = None
    HAS_PUPPETEER = False

logger = get_logger(__name__)

# Separate router for MCP tools to avoid route conflicts
router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


@router.get("/mcp-tools", response_model=Dict[str, Any])
async def list_mcp_tools(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all available MCP tools organized by server"""
    tools_by_server = {}
    total_tools = 0
    errors = []
    
    try:
        # Database MCP Server - use the session directly
        try:
            db_server = DatabaseMCPServer(db=db)
            db_tools = await db_server.list_tools()
            if db_tools:
                tools_by_server["database"] = {
                    "name": "Database",
                    "description": "Query tigers, facilities, and investigations",
                    "tools": db_tools
                }
                total_tools += len(db_tools)
        except Exception as e:
            error_msg = f"Error loading database tools: {str(e)}"
            logger.warning(error_msg, exc_info=True)
            errors.append({"server": "database", "error": error_msg})
    
    except Exception as e:
        error_msg = f"Failed to initialize database server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append({"server": "database", "error": error_msg})
    
    try:
        # Firecrawl MCP Server
        try:
            firecrawl_server = FirecrawlMCPServer()
            firecrawl_tools = await firecrawl_server.list_tools()
            if firecrawl_tools:
                tools_by_server["firecrawl"] = {
                    "name": "Firecrawl",
                    "description": "Web search and scraping",
                    "tools": firecrawl_tools
                }
                total_tools += len(firecrawl_tools)
        except Exception as e:
            error_msg = f"Error loading firecrawl tools: {str(e)}"
            logger.warning(error_msg, exc_info=True)
            errors.append({"server": "firecrawl", "error": error_msg})
    except Exception as e:
        error_msg = f"Failed to initialize firecrawl server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append({"server": "firecrawl", "error": error_msg})
    
    try:
        # TigerID MCP Server
        try:
            tiger_id_server = TigerIDMCPServer()
            tiger_tools = await tiger_id_server.list_tools()
            if tiger_tools:
                tools_by_server["tiger_id"] = {
                    "name": "Tiger Identification",
                    "description": "Identify tigers from images",
                    "tools": tiger_tools
                }
                total_tools += len(tiger_tools)
        except Exception as e:
            error_msg = f"Error loading tiger ID tools: {str(e)}"
            logger.warning(error_msg, exc_info=True)
            errors.append({"server": "tiger_id", "error": error_msg})
    except Exception as e:
        error_msg = f"Failed to initialize tiger ID server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append({"server": "tiger_id", "error": error_msg})
    
    try:
        # YouTube MCP Server
        try:
            youtube_server = YouTubeMCPServer()
            youtube_tools = await youtube_server.list_tools()
            if youtube_tools:
                tools_by_server["youtube"] = {
                    "name": "YouTube",
                    "description": "Search YouTube videos",
                    "tools": youtube_tools
                }
                total_tools += len(youtube_tools)
        except Exception as e:
            error_msg = f"Error loading YouTube tools: {str(e)}"
            logger.warning(error_msg, exc_info=True)
            errors.append({"server": "youtube", "error": error_msg})
    except Exception as e:
        error_msg = f"Failed to initialize YouTube server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append({"server": "youtube", "error": error_msg})
    
    try:
        # Meta MCP Server
        try:
            meta_server = MetaMCPServer()
            meta_tools = await meta_server.list_tools()
            if meta_tools:
                tools_by_server["meta"] = {
                    "name": "Meta",
                    "description": "Search Meta/Facebook pages",
                    "tools": meta_tools
                }
                total_tools += len(meta_tools)
        except Exception as e:
            error_msg = f"Error loading Meta tools: {str(e)}"
            logger.warning(error_msg, exc_info=True)
            errors.append({"server": "meta", "error": error_msg})
    except Exception as e:
        error_msg = f"Failed to initialize Meta server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append({"server": "meta", "error": error_msg})
    
    try:
        # Puppeteer MCP Server (optional)
        settings = get_settings()
        if HAS_PUPPETEER and settings.puppeteer.enabled:
            try:
                puppeteer_server = PuppeteerMCPServer()
                puppeteer_tools = await puppeteer_server.list_tools()
                if puppeteer_tools:
                    tools_by_server["puppeteer"] = {
                        "name": "Puppeteer",
                        "description": "Browser automation and scraping",
                        "tools": puppeteer_tools
                    }
                    total_tools += len(puppeteer_tools)
            except Exception as e:
                error_msg = f"Error loading Puppeteer tools: {str(e)}"
                logger.warning(error_msg, exc_info=True)
                errors.append({"server": "puppeteer", "error": error_msg})
    except Exception as e:
        error_msg = f"Failed to initialize Puppeteer server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append({"server": "puppeteer", "error": error_msg})
    
    # Also include high-level investigation tools
    investigation_tools = [
        {
            "name": "web_search",
            "description": "Search the web for information",
            "server": "firecrawl"
        },
        {
            "name": "reverse_image_search",
            "description": "Search for images using reverse image search",
            "server": "image_search"
        },
        {
            "name": "news_search",
            "description": "Search news articles",
            "server": "news_monitoring"
        },
        {
            "name": "generate_leads",
            "description": "Generate investigation leads",
            "server": "lead_generation"
        },
        {
            "name": "relationship_analysis",
            "description": "Analyze relationships between entities",
            "server": "relationship_analysis"
        },
        {
            "name": "evidence_compilation",
            "description": "Compile and organize evidence",
            "server": "evidence_compilation"
        }
    ]
    
    tools_by_server["investigation_tools"] = {
        "name": "Investigation Tools",
        "description": "High-level investigation tools",
        "tools": investigation_tools
    }
    
    # Count all tools including investigation_tools
    total_tools_all = sum(len(server["tools"]) for server in tools_by_server.values())
    
    # If no MCP server tools were loaded (only investigation_tools), and we have errors, return error response
    # Note: investigation_tools are always available, so we check if MCP server tools failed
    mcp_server_tools_count = total_tools_all - len(investigation_tools)
    if mcp_server_tools_count == 0 and len(errors) > 0:
        error_summary = "; ".join([e["error"] for e in errors[:3]])  # Show first 3 errors
        logger.error(f"Failed to load any MCP server tools. Errors: {error_summary}")
        # Don't raise exception - still return investigation_tools, but include errors
        # This allows the frontend to show investigation_tools even if MCP servers fail
    
    response = {
        "success": True,
        "data": {
            "servers": tools_by_server,
            "total_tools": total_tools_all,
            "mcp_tools_count": mcp_server_tools_count
        }
    }
    
    # Include errors in response if any occurred (but still return tools if some loaded)
    if errors:
        response["data"]["errors"] = errors
        response["data"]["partial_success"] = mcp_server_tools_count > 0
        logger.warning(f"Some MCP servers failed to load. {len(errors)} errors. MCP tools loaded: {mcp_server_tools_count}")
    
    return response

