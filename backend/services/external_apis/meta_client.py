"""Meta Graph API client for Facebook pages and posts"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.services.external_apis.base_client import BaseAPIClient
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class MetaClient(BaseAPIClient):
    """Client for Meta Graph API
    
    Meta Graph API provides access to:
    - Page information and search
    - Post details and comments
    - Public content search
    
    Note: Meta Graph API documentation: https://developers.facebook.com/docs/graph-api
    Platform Terms: https://developers.facebook.com/terms/dfc_platform_terms/
    Data Use Policy: https://developers.meta.com/horizon/policy/data-use/
    """
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        api_version: str = "v19.0",
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Meta API client
        
        Args:
            access_token: OAuth access token
            app_id: Facebook App ID
            app_secret: Facebook App Secret
            api_version: Graph API version (default: v19.0)
            base_url: Base URL (default: https://graph.facebook.com/{api_version})
            timeout: Request timeout in seconds
        """
        if base_url is None:
            base_url = f"https://graph.facebook.com/{api_version}"
        
        # Meta API uses access_token, not api_key
        # Store it in api_key for BaseAPIClient compatibility
        super().__init__(api_key=access_token, base_url=base_url, timeout=timeout)
        self.access_token = access_token
        self.app_id = app_id
        self.app_secret = app_secret
        self.api_version = api_version
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers (Meta API uses token in query params, not headers)"""
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
        Override to add access_token as parameter for Meta Graph API
        """
        if params is None:
            params = {}
        
        # Add access_token as parameter (Meta Graph API requirement)
        if self.access_token:
            params["access_token"] = self.access_token
        
        # Call parent method
        return await super()._request(method, endpoint, params, data, headers)
    
    async def health_check(self) -> bool:
        """Check if Meta Graph API is accessible"""
        try:
            # Test with a simple API call to check token validity
            # Using /me endpoint with proper permissions
            response = await self._request("GET", "/me", params={"fields": "id"})
            return "id" in response or "error" not in response
        except Exception as e:
            logger.warning("Meta health check failed", error=str(e))
            # Try a different endpoint that doesn't require user token
            try:
                # Check app token validity
                if self.app_id and self.app_secret:
                    response = await self._request(
                        "GET",
                        f"/oauth/access_token",
                        params={
                            "client_id": self.app_id,
                            "client_secret": self.app_secret,
                            "grant_type": "client_credentials"
                        }
                    )
                    return "access_token" in response or "error" not in response
            except:
                pass
            return False
    
    async def get_page_info(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Get page information
        
        Args:
            page_id: Facebook page ID or username
        
        Returns:
            Page information dictionary or None if not found
        """
        params = {
            "fields": "id,name,username,about,category,category_list,fan_count,"
                     "followers_count,likes,link,phone,website,location,"
                     "verification_status,picture"
        }
        
        try:
            response = await self._request("GET", f"/{page_id}", params=params)
            
            if "error" in response:
                logger.warning(
                    "Meta API error",
                    page_id=page_id,
                    error=response.get("error", {})
                )
                return None
            
            return {
                "page_id": response.get("id", ""),
                "name": response.get("name", ""),
                "username": response.get("username", ""),
                "about": response.get("about", ""),
                "category": response.get("category", ""),
                "categories": [
                    cat.get("name", "") 
                    for cat in response.get("category_list", [])
                ],
                "fan_count": response.get("fan_count", 0),
                "followers_count": response.get("followers_count", 0),
                "likes": response.get("likes", 0),
                "link": response.get("link", ""),
                "phone": response.get("phone", ""),
                "website": response.get("website", ""),
                "location": response.get("location", {}),
                "verification_status": response.get("verification_status", ""),
                "picture": response.get("picture", {}).get("data", {}).get("url", ""),
                "url": response.get("link", f"https://www.facebook.com/{response.get('id', '')}")
            }
        except Exception as e:
            logger.error(
                "Failed to get Meta page info",
                page_id=page_id,
                error=str(e)
            )
            return None
    
    async def search_pages(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for Facebook pages
        
        Args:
            query: Search query string
            limit: Maximum number of results (default: 10)
        
        Returns:
            List of page information dictionaries
        """
        params = {
            "q": query,
            "type": "page",
            "limit": limit,
            "fields": "id,name,username,about,category,fan_count,link,picture"
        }
        
        try:
            response = await self._request("GET", "/search", params=params)
            
            if "error" in response:
                logger.warning("Meta search error", error=response.get("error", {}))
                return []
            
            pages = []
            for item in response.get("data", []):
                pages.append({
                    "page_id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "username": item.get("username", ""),
                    "about": item.get("about", ""),
                    "category": item.get("category", ""),
                    "fan_count": item.get("fan_count", 0),
                    "link": item.get("link", ""),
                    "picture": item.get("picture", {}).get("data", {}).get("url", ""),
                    "url": item.get("link", f"https://www.facebook.com/{item.get('id', '')}")
                })
            
            return pages
        except Exception as e:
            logger.error("Meta page search failed", query=query, error=str(e))
            return []
    
    async def get_page_posts(
        self,
        page_id: str,
        limit: int = 10,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get posts from a page
        
        Args:
            page_id: Facebook page ID
            limit: Maximum number of results (default: 10)
            since: Filter posts since this date
            until: Filter posts until this date
        
        Returns:
            List of post information dictionaries
        """
        params = {
            "fields": "id,message,story,created_time,updated_time,shares,"
                     "likes.summary(true),comments.summary(true),permalink_url",
            "limit": limit
        }
        
        if since:
            params["since"] = int(since.timestamp())
        if until:
            params["until"] = int(until.timestamp())
        
        try:
            response = await self._request(
                "GET",
                f"/{page_id}/posts",
                params=params
            )
            
            if "error" in response:
                logger.warning(
                    "Meta API error getting posts",
                    page_id=page_id,
                    error=response.get("error", {})
                )
                return []
            
            posts = []
            for item in response.get("data", []):
                likes = item.get("likes", {}).get("summary", {}).get("total_count", 0)
                comments = item.get("comments", {}).get("summary", {}).get("total_count", 0)
                
                posts.append({
                    "post_id": item.get("id", ""),
                    "message": item.get("message", ""),
                    "story": item.get("story", ""),
                    "created_time": item.get("created_time", ""),
                    "updated_time": item.get("updated_time", ""),
                    "shares": item.get("shares", {}).get("count", 0),
                    "like_count": likes,
                    "comment_count": comments,
                    "permalink_url": item.get("permalink_url", ""),
                    "url": item.get("permalink_url", "")
                })
            
            return posts
        except Exception as e:
            logger.error(
                "Failed to get Meta page posts",
                page_id=page_id,
                error=str(e)
            )
            return []
    
    async def get_post_details(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a post
        
        Args:
            post_id: Facebook post ID
        
        Returns:
            Post details dictionary or None if not found
        """
        params = {
            "fields": "id,message,story,created_time,updated_time,from,"
                     "shares,likes.summary(true),comments.summary(true),"
                     "permalink_url,attachments"
        }
        
        try:
            response = await self._request("GET", f"/{post_id}", params=params)
            
            if "error" in response:
                logger.warning(
                    "Meta API error getting post",
                    post_id=post_id,
                    error=response.get("error", {})
                )
                return None
            
            likes = response.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = response.get("comments", {}).get("summary", {}).get("total_count", 0)
            
            return {
                "post_id": response.get("id", ""),
                "message": response.get("message", ""),
                "story": response.get("story", ""),
                "created_time": response.get("created_time", ""),
                "updated_time": response.get("updated_time", ""),
                "from": response.get("from", {}),
                "shares": response.get("shares", {}).get("count", 0),
                "like_count": likes,
                "comment_count": comments,
                "permalink_url": response.get("permalink_url", ""),
                "attachments": response.get("attachments", {}).get("data", []),
                "url": response.get("permalink_url", "")
            }
        except Exception as e:
            logger.error(
                "Failed to get Meta post details",
                post_id=post_id,
                error=str(e)
            )
            return None
    
    async def get_post_comments(
        self,
        post_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get comments for a post
        
        Args:
            post_id: Facebook post ID
            limit: Maximum number of results (default: 10)
        
        Returns:
            List of comment dictionaries
        """
        params = {
            "fields": "id,message,from,created_time,like_count,comment_count",
            "limit": limit
        }
        
        try:
            response = await self._request(
                "GET",
                f"/{post_id}/comments",
                params=params
            )
            
            if "error" in response:
                logger.warning(
                    "Meta API error getting comments",
                    post_id=post_id,
                    error=response.get("error", {})
                )
                return []
            
            comments = []
            for item in response.get("data", []):
                comments.append({
                    "comment_id": item.get("id", ""),
                    "message": item.get("message", ""),
                    "from": item.get("from", {}),
                    "created_time": item.get("created_time", ""),
                    "like_count": item.get("like_count", 0),
                    "comment_count": item.get("comment_count", 0)
                })
            
            return comments
        except Exception as e:
            logger.error(
                "Failed to get Meta post comments",
                post_id=post_id,
                error=str(e)
            )
            return []
    
    async def search_public_posts(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for public posts
        
        Note: Public post search has limited availability and requires
        appropriate permissions. Results may be restricted.
        
        Args:
            query: Search query string
            limit: Maximum number of results (default: 10)
        
        Returns:
            List of post information dictionaries
        """
        # Note: Public post search is limited in Graph API
        # This may require different endpoints or permissions
        # For now, we'll search pages and get their posts
        
        try:
            # First search for relevant pages
            pages = await self.search_pages(query, limit=5)
            
            all_posts = []
            for page in pages[:3]:  # Limit to first 3 pages to avoid rate limits
                page_id = page.get("page_id")
                if page_id:
                    posts = await self.get_page_posts(page_id, limit=limit // 3 + 1)
                    all_posts.extend(posts)
                    
                    if len(all_posts) >= limit:
                        break
            
            return all_posts[:limit]
        except Exception as e:
            logger.error("Meta public post search failed", query=query, error=str(e))
            return []

