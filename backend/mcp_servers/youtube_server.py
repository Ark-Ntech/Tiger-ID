"""YouTube MCP server for YouTube Data API v3"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.services.external_apis.factory import get_api_clients
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class YouTubeMCPServer(MCPServerBase):
    """MCP server for YouTube Data API v3"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube MCP server
        
        Args:
            api_key: YouTube API key (optional, will use from config if not provided)
        """
        super().__init__("youtube")
        
        # Get YouTube client from factory
        clients = get_api_clients()
        self.client = clients.get("youtube")
        
        # If client not available, try to create it
        if not self.client:
            from backend.services.external_apis.youtube_client import YouTubeClient
            from backend.config.settings import get_settings
            settings = get_settings()
            api_key = api_key or settings.external_apis.youtube_api_key
            if api_key:
                self.client = YouTubeClient(api_key=api_key)
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        self.tools = {
            "youtube_search_videos": MCPTool(
                name="youtube_search_videos",
                description="Search for videos on YouTube",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "order": {
                            "type": "string",
                            "description": "Sort order",
                            "enum": ["relevance", "date", "rating", "viewCount", "title"],
                            "default": "relevance"
                        },
                        "published_after": {
                            "type": "string",
                            "description": "Filter videos published after this date (ISO format)"
                        }
                    },
                    "required": ["query"]
                },
                handler=self._handle_search_videos
            ),
            "youtube_get_channel": MCPTool(
                name="youtube_get_channel",
                description="Get channel information",
                parameters={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "YouTube channel ID"
                        }
                    },
                    "required": ["channel_id"]
                },
                handler=self._handle_get_channel
            ),
            "youtube_get_channel_videos": MCPTool(
                name="youtube_get_channel_videos",
                description="Get videos from a channel",
                parameters={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "YouTube channel ID"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "order": {
                            "type": "string",
                            "description": "Sort order",
                            "enum": ["date", "rating", "relevance", "title", "videoCount", "viewCount"],
                            "default": "date"
                        }
                    },
                    "required": ["channel_id"]
                },
                handler=self._handle_get_channel_videos
            ),
            "youtube_search_channels": MCPTool(
                name="youtube_search_channels",
                description="Search for channels on YouTube",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["query"]
                },
                handler=self._handle_search_channels
            ),
            "youtube_get_video_details": MCPTool(
                name="youtube_get_video_details",
                description="Get detailed information about a video",
                parameters={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID"
                        }
                    },
                    "required": ["video_id"]
                },
                handler=self._handle_get_video_details
            ),
            "youtube_get_comments": MCPTool(
                name="youtube_get_comments",
                description="Get comments for a video",
                parameters={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "order": {
                            "type": "string",
                            "description": "Sort order",
                            "enum": ["relevance", "time"],
                            "default": "relevance"
                        }
                    },
                    "required": ["video_id"]
                },
                handler=self._handle_get_comments
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
            return {"error": "YouTube client not initialized. Check API key configuration."}
        
        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error("YouTube tool call failed", tool=tool_name, error=str(e))
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return []
    
    async def _handle_search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance",
        published_after: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle video search"""
        if not self.client:
            logger.warning("YouTube API key not configured - returning empty result")
            return {
                "query": query,
                "videos": [],
                "count": 0,
                "warning": "YouTube API key not configured. Set YOUTUBE_API_KEY to enable YouTube search."
            }
        
        try:
            published_after_dt = None
            if published_after:
                try:
                    published_after_dt = datetime.fromisoformat(published_after.replace("Z", "+00:00"))
                except:
                    logger.warning("Invalid date format", date=published_after)
            
            videos = await self.client.search_videos(
                query=query,
                max_results=max_results,
                order=order,
                published_after=published_after_dt
            )
            
            logger.info("YouTube video search completed", query=query[:50], count=len(videos))
            
            return {
                "query": query,
                "videos": videos,
                "count": len(videos)
            }
        except Exception as e:
            logger.error("YouTube video search failed", query=query, error=str(e))
            return {"error": str(e), "query": query, "videos": [], "count": 0}
    
    async def _handle_get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Handle get channel info"""
        if not self.client:
            logger.warning("YouTube API key not configured - returning empty result")
            return {
                "channel_id": channel_id,
                "error": "YouTube API key not configured. Set YOUTUBE_API_KEY to enable YouTube features."
            }
        
        try:
            channel_info = await self.client.get_channel_info(channel_id)
            
            if not channel_info:
                return {"error": "Channel not found", "channel_id": channel_id}
            
            logger.info("YouTube channel info retrieved", channel_id=channel_id)
            
            return {
                "channel_id": channel_id,
                "channel": channel_info
            }
        except Exception as e:
            logger.error("Failed to get YouTube channel", channel_id=channel_id, error=str(e))
            return {"error": str(e), "channel_id": channel_id}
    
    async def _handle_get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 10,
        order: str = "date"
    ) -> Dict[str, Any]:
        """Handle get channel videos"""
        if not self.client:
            logger.warning("YouTube API key not configured - returning empty result")
            return {
                "channel_id": channel_id,
                "videos": [],
                "count": 0,
                "warning": "YouTube API key not configured. Set YOUTUBE_API_KEY to enable YouTube features."
            }
        
        try:
            videos = await self.client.get_channel_videos(
                channel_id=channel_id,
                max_results=max_results,
                order=order
            )
            
            logger.info("YouTube channel videos retrieved", channel_id=channel_id, count=len(videos))
            
            return {
                "channel_id": channel_id,
                "videos": videos,
                "count": len(videos)
            }
        except Exception as e:
            logger.error("Failed to get YouTube channel videos", channel_id=channel_id, error=str(e))
            return {"error": str(e), "channel_id": channel_id, "videos": [], "count": 0}
    
    async def _handle_search_channels(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Handle channel search"""
        if not self.client:
            logger.warning("YouTube API key not configured - returning empty result")
            return {
                "query": query,
                "channels": [],
                "count": 0,
                "warning": "YouTube API key not configured. Set YOUTUBE_API_KEY to enable YouTube search."
            }
        
        try:
            channels = await self.client.search_channels(query=query, max_results=max_results)
            
            logger.info("YouTube channel search completed", query=query[:50], count=len(channels))
            
            return {
                "query": query,
                "channels": channels,
                "count": len(channels)
            }
        except Exception as e:
            logger.error("YouTube channel search failed", query=query, error=str(e))
            return {"error": str(e), "query": query, "channels": [], "count": 0}
    
    async def _handle_get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Handle get video details"""
        if not self.client:
            logger.warning("YouTube API key not configured - returning empty result")
            return {
                "video_id": video_id,
                "error": "YouTube API key not configured. Set YOUTUBE_API_KEY to enable YouTube features."
            }
        
        try:
            video_details = await self.client.get_video_details(video_id)
            
            if not video_details:
                return {"error": "Video not found", "video_id": video_id}
            
            logger.info("YouTube video details retrieved", video_id=video_id)
            
            return {
                "video_id": video_id,
                "video": video_details
            }
        except Exception as e:
            logger.error("Failed to get YouTube video details", video_id=video_id, error=str(e))
            return {"error": str(e), "video_id": video_id}
    
    async def _handle_get_comments(
        self,
        video_id: str,
        max_results: int = 10,
        order: str = "relevance"
    ) -> Dict[str, Any]:
        """Handle get video comments"""
        if not self.client:
            logger.warning("YouTube API key not configured - returning empty result")
            return {
                "video_id": video_id,
                "comments": [],
                "count": 0,
                "warning": "YouTube API key not configured. Set YOUTUBE_API_KEY to enable YouTube features."
            }
        
        try:
            comments = await self.client.get_video_comments(
                video_id=video_id,
                max_results=max_results,
                order=order
            )
            
            logger.info("YouTube video comments retrieved", video_id=video_id, count=len(comments))
            
            return {
                "video_id": video_id,
                "comments": comments,
                "count": len(comments)
            }
        except Exception as e:
            logger.error("Failed to get YouTube video comments", video_id=video_id, error=str(e))
            return {"error": str(e), "video_id": video_id, "comments": [], "count": 0}

