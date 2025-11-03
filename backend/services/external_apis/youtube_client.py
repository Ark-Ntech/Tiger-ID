"""YouTube Data API v3 client for video and channel information"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.services.external_apis.base_client import BaseAPIClient
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class YouTubeClient(BaseAPIClient):
    """Client for YouTube Data API v3
    
    YouTube Data API provides access to:
    - Video search and details
    - Channel information
    - Comments and engagement metrics
    
    Note: YouTube API documentation: https://developers.google.com/youtube/v3
    Terms of Service: https://developers.google.com/youtube/terms/api-services-terms-of-service
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://www.googleapis.com/youtube/v3",
        timeout: int = 30
    ):
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
        # YouTube API uses key as query parameter, not in headers
        # We'll override the request method to handle this
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers (YouTube API doesn't use auth headers)"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Override to add API key as 'key' parameter for YouTube API
        """
        if params is None:
            params = {}
        
        # Add API key as 'key' parameter (YouTube API requirement)
        if self.api_key:
            params["key"] = self.api_key
        
        # Call parent method
        return await super()._request(method, endpoint, params, data, headers)
    
    async def health_check(self) -> bool:
        """Check if YouTube API is accessible"""
        try:
            # Simple test request - search for a common term with maxResults=1
            params = {
                "part": "id",
                "q": "test",
                "maxResults": 1,
                "type": "video"
            }
            response = await self._request("GET", "/search", params=params)
            return "items" in response
        except Exception as e:
            logger.warning("YouTube health check failed", error=str(e))
            return False
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance",
        published_after: Optional[datetime] = None,
        region_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for videos on YouTube
        
        Args:
            query: Search query string
            max_results: Maximum number of results (default: 10, max: 50)
            order: Sort order (relevance, date, rating, viewCount, title)
            published_after: Filter videos published after this date
            region_code: ISO 3166-1 alpha-2 country code for region-specific results
        
        Returns:
            List of video information dictionaries
        """
        if max_results > 50:
            max_results = 50
        
        params = {
            "part": "snippet,statistics,contentDetails",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": order
        }
        
        if published_after:
            params["publishedAfter"] = published_after.isoformat() + "Z"
        
        if region_code:
            params["regionCode"] = region_code
        
        try:
            response = await self._request("GET", "/search", params=params)
            videos = []
            
            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item.get("snippet", {})
                
                # Get additional details for each video
                video_details = await self.get_video_details(video_id)
                
                # Handle case where video_details might be None
                if video_details:
                    statistics = {
                        "viewCount": video_details.get("view_count", 0),
                        "likeCount": video_details.get("like_count", 0),
                        "commentCount": video_details.get("comment_count", 0)
                    }
                    duration = video_details.get("duration", "")
                    tags = video_details.get("tags", [])
                else:
                    statistics = {}
                    duration = ""
                    tags = []
                
                videos.append({
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "channel_id": snippet.get("channelId", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "statistics": statistics,
                    "duration": duration,
                    "tags": tags
                })
            
            return videos
        except Exception as e:
            logger.error("YouTube video search failed", query=query, error=str(e))
            return []
    
    async def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information
        
        Args:
            channel_id: YouTube channel ID
        
        Returns:
            Channel information dictionary or None if not found
        """
        params = {
            "part": "snippet,statistics,contentDetails,brandingSettings",
            "id": channel_id
        }
        
        try:
            response = await self._request("GET", "/channels", params=params)
            items = response.get("items", [])
            
            if not items:
                return None
            
            item = items[0]
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            
            return {
                "channel_id": channel_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "custom_url": snippet.get("customUrl", ""),
                "published_at": snippet.get("publishedAt", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                "country": snippet.get("country", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "subscriber_count": int(statistics.get("subscriberCount", 0)),
                "video_count": int(statistics.get("videoCount", 0)),
                "upload_playlist_id": content_details.get("relatedPlaylists", {}).get("uploads", ""),
                "url": f"https://www.youtube.com/channel/{channel_id}"
            }
        except Exception as e:
            logger.error(
                "Failed to get YouTube channel info",
                channel_id=channel_id,
                error=str(e)
            )
            return None
    
    async def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 10,
        order: str = "date"
    ) -> List[Dict[str, Any]]:
        """
        Get videos from a channel
        
        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of results (default: 10, max: 50)
            order: Sort order (date, rating, relevance, title, videoCount, viewCount)
        
        Returns:
            List of video information dictionaries
        """
        if max_results > 50:
            max_results = 50
        
        try:
            # First, get the uploads playlist ID
            channel_info = await self.get_channel_info(channel_id)
            if not channel_info:
                return []
            
            upload_playlist_id = channel_info.get("upload_playlist_id")
            if not upload_playlist_id:
                return []
            
            # Get videos from the uploads playlist
            params = {
                "part": "snippet,contentDetails",
                "playlistId": upload_playlist_id,
                "maxResults": max_results
            }
            
            response = await self._request("GET", "/playlistItems", params=params)
            videos = []
            
            for item in response.get("items", []):
                video_id = item["snippet"]["resourceId"]["videoId"]
                video_details = await self.get_video_details(video_id)
                
                # Handle case where video_details might be None
                if video_details:
                    statistics = {
                        "viewCount": video_details.get("view_count", 0),
                        "likeCount": video_details.get("like_count", 0),
                        "commentCount": video_details.get("comment_count", 0)
                    }
                    duration = video_details.get("duration", "")
                else:
                    statistics = {}
                    duration = ""
                
                snippet = item.get("snippet", {})
                videos.append({
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "statistics": statistics,
                    "duration": duration
                })
            
            return videos
        except Exception as e:
            logger.error(
                "Failed to get YouTube channel videos",
                channel_id=channel_id,
                error=str(e)
            )
            return []
    
    async def search_channels(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for channels on YouTube
        
        Args:
            query: Search query string
            max_results: Maximum number of results (default: 10, max: 50)
        
        Returns:
            List of channel information dictionaries
        """
        if max_results > 50:
            max_results = 50
        
        params = {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results
        }
        
        try:
            response = await self._request("GET", "/search", params=params)
            channels = []
            
            for item in response.get("items", []):
                channel_id = item["id"]["channelId"]
                channel_info = await self.get_channel_info(channel_id)
                
                if channel_info:
                    channels.append(channel_info)
            
            return channels
        except Exception as e:
            logger.error("YouTube channel search failed", query=query, error=str(e))
            return []
    
    async def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a video
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Video details dictionary or None if not found
        """
        params = {
            "part": "snippet,statistics,contentDetails,status",
            "id": video_id
        }
        
        try:
            response = await self._request("GET", "/videos", params=params)
            items = response.get("items", [])
            
            if not items:
                return None
            
            item = items[0]
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            
            return {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "duration": content_details.get("duration", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }
        except Exception as e:
            logger.error(
                "Failed to get YouTube video details",
                video_id=video_id,
                error=str(e)
            )
            return None
    
    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 10,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Get comments for a video
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of results (default: 10, max: 100)
            order: Sort order (relevance, time)
        
        Returns:
            List of comment dictionaries
        """
        if max_results > 100:
            max_results = 100
        
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": max_results,
            "order": order,
            "textFormat": "plainText"
        }
        
        try:
            response = await self._request("GET", "/commentThreads", params=params)
            comments = []
            
            for item in response.get("items", []):
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                
                comments.append({
                    "comment_id": item.get("id", ""),
                    "author": snippet.get("authorDisplayName", ""),
                    "text": snippet.get("textDisplay", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "updated_at": snippet.get("updatedAt", ""),
                    "like_count": int(snippet.get("likeCount", 0)),
                    "reply_count": int(item.get("snippet", {}).get("totalReplyCount", 0))
                })
            
            return comments
        except Exception as e:
            logger.error(
                "Failed to get YouTube video comments",
                video_id=video_id,
                error=str(e)
            )
            return []

