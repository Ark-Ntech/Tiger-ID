"""Meta MCP server for Facebook Graph API"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.services.external_apis.factory import get_api_clients
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class MetaMCPServer(MCPServerBase):
    """MCP server for Meta Graph API"""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Meta MCP server
        
        Args:
            access_token: Meta access token (optional, will use from config if not provided)
        """
        super().__init__("meta")
        
        # Get Meta client from factory
        clients = get_api_clients()
        self.client = clients.get("meta")
        
        # If client not available, try to create it
        if not self.client:
            from backend.services.external_apis.meta_client import MetaClient
            from backend.config.settings import get_settings
            settings = get_settings()
            access_token = access_token or settings.external_apis.meta_access_token
            app_id = settings.external_apis.meta_app_id
            app_secret = settings.external_apis.meta_app_secret
            if access_token:
                self.client = MetaClient(
                    access_token=access_token,
                    app_id=app_id,
                    app_secret=app_secret
                )
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        self.tools = {
            "meta_get_page": MCPTool(
                name="meta_get_page",
                description="Get Facebook page information",
                parameters={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Facebook page ID or username"
                        }
                    },
                    "required": ["page_id"]
                },
                handler=self._handle_get_page
            ),
            "meta_search_pages": MCPTool(
                name="meta_search_pages",
                description="Search for Facebook pages",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1
                        }
                    },
                    "required": ["query"]
                },
                handler=self._handle_search_pages
            ),
            "meta_get_page_posts": MCPTool(
                name="meta_get_page_posts",
                description="Get posts from a Facebook page",
                parameters={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Facebook page ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1
                        },
                        "since": {
                            "type": "string",
                            "description": "Filter posts since this date (ISO format)"
                        },
                        "until": {
                            "type": "string",
                            "description": "Filter posts until this date (ISO format)"
                        }
                    },
                    "required": ["page_id"]
                },
                handler=self._handle_get_page_posts
            ),
            "meta_get_post_details": MCPTool(
                name="meta_get_post_details",
                description="Get detailed information about a post",
                parameters={
                    "type": "object",
                    "properties": {
                        "post_id": {
                            "type": "string",
                            "description": "Facebook post ID"
                        }
                    },
                    "required": ["post_id"]
                },
                handler=self._handle_get_post_details
            ),
            "meta_get_comments": MCPTool(
                name="meta_get_comments",
                description="Get comments for a post",
                parameters={
                    "type": "object",
                    "properties": {
                        "post_id": {
                            "type": "string",
                            "description": "Facebook post ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1
                        }
                    },
                    "required": ["post_id"]
                },
                handler=self._handle_get_comments
            ),
            "meta_search_posts": MCPTool(
                name="meta_search_posts",
                description="Search for public posts (limited availability)",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1
                        }
                    },
                    "required": ["query"]
                },
                handler=self._handle_search_posts
            )
        }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
        
        if not self.client:
            return {"error": "Meta client not initialized. Check access token configuration."}
        
        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error("Meta tool call failed", tool=tool_name, error=str(e))
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return []
    
    async def _handle_get_page(self, page_id: str) -> Dict[str, Any]:
        """Handle get page info"""
        if not self.client:
            logger.warning("Meta API credentials not configured - returning empty result")
            return {
                "page_id": page_id,
                "error": "Meta API credentials not configured. Set META_ACCESS_TOKEN to enable Meta features."
            }
        
        try:
            page_info = await self.client.get_page_info(page_id)
            
            if not page_info:
                return {"error": "Page not found", "page_id": page_id}
            
            logger.info("Meta page info retrieved", page_id=page_id)
            
            return {
                "page_id": page_id,
                "page": page_info
            }
        except Exception as e:
            logger.error("Failed to get Meta page", page_id=page_id, error=str(e))
            return {"error": str(e), "page_id": page_id}
    
    async def _handle_search_pages(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Handle page search"""
        if not self.client:
            logger.warning("Meta API credentials not configured - returning empty result")
            return {
                "query": query,
                "pages": [],
                "count": 0,
                "warning": "Meta API credentials not configured. Set META_ACCESS_TOKEN to enable Meta search."
            }
        
        try:
            pages = await self.client.search_pages(query=query, limit=limit)
            
            logger.info("Meta page search completed", query=query[:50], count=len(pages))
            
            return {
                "query": query,
                "pages": pages,
                "count": len(pages)
            }
        except Exception as e:
            logger.error("Meta page search failed", query=query, error=str(e))
            return {"error": str(e), "query": query, "pages": [], "count": 0}
    
    async def _handle_get_page_posts(
        self,
        page_id: str,
        limit: int = 10,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle get page posts"""
        if not self.client:
            logger.warning("Meta API credentials not configured - returning empty result")
            return {
                "page_id": page_id,
                "posts": [],
                "count": 0,
                "warning": "Meta API credentials not configured. Set META_ACCESS_TOKEN to enable Meta features."
            }
        
        try:
            since_dt = None
            until_dt = None
            
            if since:
                try:
                    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                except:
                    logger.warning("Invalid since date format", date=since)
            
            if until:
                try:
                    until_dt = datetime.fromisoformat(until.replace("Z", "+00:00"))
                except:
                    logger.warning("Invalid until date format", date=until)
            
            posts = await self.client.get_page_posts(
                page_id=page_id,
                limit=limit,
                since=since_dt,
                until=until_dt
            )
            
            logger.info("Meta page posts retrieved", page_id=page_id, count=len(posts))
            
            return {
                "page_id": page_id,
                "posts": posts,
                "count": len(posts)
            }
        except Exception as e:
            logger.error("Failed to get Meta page posts", page_id=page_id, error=str(e))
            return {"error": str(e), "page_id": page_id, "posts": [], "count": 0}
    
    async def _handle_get_post_details(self, post_id: str) -> Dict[str, Any]:
        """Handle get post details"""
        if not self.client:
            logger.warning("Meta API credentials not configured - returning empty result")
            return {
                "post_id": post_id,
                "error": "Meta API credentials not configured. Set META_ACCESS_TOKEN to enable Meta features."
            }
        
        try:
            post_details = await self.client.get_post_details(post_id)
            
            if not post_details:
                return {"error": "Post not found", "post_id": post_id}
            
            logger.info("Meta post details retrieved", post_id=post_id)
            
            return {
                "post_id": post_id,
                "post": post_details
            }
        except Exception as e:
            logger.error("Failed to get Meta post details", post_id=post_id, error=str(e))
            return {"error": str(e), "post_id": post_id}
    
    async def _handle_get_comments(self, post_id: str, limit: int = 10) -> Dict[str, Any]:
        """Handle get post comments"""
        if not self.client:
            logger.warning("Meta API credentials not configured - returning empty result")
            return {
                "post_id": post_id,
                "comments": [],
                "count": 0,
                "warning": "Meta API credentials not configured. Set META_ACCESS_TOKEN to enable Meta features."
            }
        
        try:
            comments = await self.client.get_post_comments(post_id=post_id, limit=limit)
            
            logger.info("Meta post comments retrieved", post_id=post_id, count=len(comments))
            
            return {
                "post_id": post_id,
                "comments": comments,
                "count": len(comments)
            }
        except Exception as e:
            logger.error("Failed to get Meta post comments", post_id=post_id, error=str(e))
            return {"error": str(e), "post_id": post_id, "comments": [], "count": 0}
    
    async def _handle_search_posts(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Handle search public posts"""
        if not self.client:
            logger.warning("Meta API credentials not configured - returning empty result")
            return {
                "query": query,
                "posts": [],
                "count": 0,
                "warning": "Meta API credentials not configured. Set META_ACCESS_TOKEN to enable Meta search."
            }
        
        try:
            posts = await self.client.search_public_posts(query=query, limit=limit)
            
            logger.info("Meta post search completed", query=query[:50], count=len(posts))
            
            return {
                "query": query,
                "posts": posts,
                "count": len(posts)
            }
        except Exception as e:
            logger.error("Meta post search failed", query=query, error=str(e))
            return {"error": str(e), "query": query, "posts": [], "count": 0}

