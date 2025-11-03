"""Firecrawl MCP server for web scraping and search"""

from typing import Dict, Any, List, Optional

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from firecrawl import FirecrawlApp
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class FirecrawlMCPServer(MCPServerBase):
    """Firecrawl MCP server for web search and scraping"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Firecrawl MCP server
        
        Args:
            api_key: Firecrawl API key
        """
        super().__init__("firecrawl")
        settings = get_settings()
        self.api_key = api_key or settings.firecrawl.api_key
        self.client = FirecrawlApp(api_key=self.api_key) if self.api_key else None
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        self.tools = {
            "firecrawl_search": MCPTool(
                name="firecrawl_search",
                description="Search the web for information",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                },
                handler=self._handle_search
            ),
            "firecrawl_scrape": MCPTool(
                name="firecrawl_scrape",
                description="Scrape a single web page",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to scrape"
                        },
                        "extract": {
                            "type": "boolean",
                            "description": "Extract structured data using LLM",
                            "default": True
                        }
                    },
                    "required": ["url"]
                },
                handler=self._handle_scrape
            ),
            "firecrawl_crawl": MCPTool(
                name="firecrawl_crawl",
                description="Crawl a website and extract all pages",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Base URL to crawl"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of pages",
                            "default": 10
                        }
                    },
                    "required": ["url"]
                },
                handler=self._handle_crawl
            ),
            "firecrawl_extract": MCPTool(
                name="firecrawl_extract",
                description="Extract structured data from a web page using LLM",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to extract from"
                        },
                        "schema": {
                            "type": "object",
                            "description": "Schema for extraction"
                        }
                    },
                    "required": ["url"]
                },
                handler=self._handle_extract
            )
        }
    
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
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return []
    
    async def _handle_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Handle web search using web search service"""
        try:
            from backend.services.web_search_service import get_web_search_service
            
            search_service = get_web_search_service()
            result = await search_service.search(query, limit=limit, provider="firecrawl")
            
            logger.info("Web search completed", query=query[:50], count=result.get("count", 0))
            
            return result
        except ImportError:
            logger.warning("Web search service not available, using fallback")
            # Fallback to empty results if service not available
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": "Web search service not available"
            }
        except Exception as e:
            logger.error("Search failed", query=query, error=str(e), exc_info=True)
            return {"error": str(e), "results": [], "query": query, "count": 0}
    
    async def _handle_scrape(self, url: str, extract: bool = True) -> Dict[str, Any]:
        """Handle page scraping"""
        if not self.client:
            logger.warning("Firecrawl API key not configured - returning empty result")
            return {
                "url": url,
                "content": "",
                "html": "",
                "extracted": None,
                "warning": "Firecrawl API key not configured. Set FIRECRAWL_API_KEY to enable web scraping."
            }
        
        try:
            result = self.client.scrape_url(url, params={
                "formats": ["markdown", "html"],
                "onlyMainContent": True
            })
            
            extracted_data = None
            if extract:
                # Use LLM extraction if available
                extracted_data = result.get("markdown", "")[:1000]  # Limit for now
            
            return {
                "url": url,
                "content": result.get("markdown", ""),
                "html": result.get("html", ""),
                "extracted": extracted_data,
                "title": result.get("metadata", {}).get("title", "")
            }
        except Exception as e:
            logger.error("Scrape failed", url=url, error=str(e))
            return {"error": str(e), "url": url}
    
    async def _handle_crawl(self, url: str, limit: int = 10) -> Dict[str, Any]:
        """Handle website crawling"""
        if not self.client:
            logger.warning("Firecrawl API key not configured - returning empty result")
            return {
                "base_url": url,
                "pages": [],
                "count": 0,
                "warning": "Firecrawl API key not configured. Set FIRECRAWL_API_KEY to enable web crawling."
            }
        
        try:
            result = self.client.crawl_url(url, params={
                "limit": limit,
                "formats": ["markdown"]
            })
            
            pages = []
            for page in result.get("data", [])[:limit]:
                pages.append({
                    "url": page.get("url"),
                    "content": page.get("markdown", "")[:500],  # Limit content
                    "title": page.get("metadata", {}).get("title", "")
                })
            
            return {
                "base_url": url,
                "pages": pages,
                "count": len(pages)
            }
        except Exception as e:
            logger.error("Crawl failed", url=url, error=str(e))
            return {"error": str(e), "base_url": url}
    
    async def _handle_extract(self, url: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle structured data extraction"""
        if not self.client:
            logger.warning("Firecrawl API key not configured - returning empty result")
            return {
                "url": url,
                "extracted": "",
                "schema": schema,
                "warning": "Firecrawl API key not configured. Set FIRECRAWL_API_KEY to enable data extraction."
            }
        
        try:
            # Scrape first
            scrape_result = await self._handle_scrape(url, extract=False)
            
            # In production, use Firecrawl's LLM extraction
            # For now, return scraped content
            return {
                "url": url,
                "extracted": scrape_result.get("content", "")[:1000],
                "schema": schema
            }
        except Exception as e:
            logger.error("Extract failed", url=url, error=str(e))
            return {"error": str(e), "url": url}
