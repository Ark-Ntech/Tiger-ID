"""Reverse image search service for web-based image search"""

from typing import Dict, Any, List, Optional
import httpx
import base64
import hashlib
from io import BytesIO

from backend.config.settings import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ImageSearchService:
    """Service for reverse image search using web APIs"""
    
    def __init__(self):
        """Initialize image search service"""
        self.settings = get_settings()
    
    async def reverse_search(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        provider: str = "google"
    ) -> Dict[str, Any]:
        """
        Perform reverse image search
        
        Args:
            image_url: URL of image to search
            image_bytes: Image bytes (alternative to image_url)
            provider: Search provider (google, tineye, yandex)
            
        Returns:
            Search results dictionary
        """
        if not image_url and not image_bytes:
            return {"error": "Either image_url or image_bytes must be provided"}
        
        try:
            if provider == "google":
                return await self._search_google_images(image_url, image_bytes)
            elif provider == "tineye":
                return await self._search_tineye(image_url, image_bytes)
            elif provider == "yandex":
                return await self._search_yandex(image_url, image_bytes)
            else:
                return await self._search_google_images(image_url, image_bytes)
        except Exception as e:
            logger.error(f"Reverse image search failed: {e}", exc_info=True)
            return {"error": str(e), "results": []}
    
    async def _search_google_images(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Search using Google Images reverse search"""
        try:
            # Download image if URL provided
            if image_url and not image_bytes:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_bytes = response.content
            
            if not image_bytes:
                return {"error": "Could not retrieve image", "results": []}
            
            # Encode image for search
            image_b64 = base64.b64encode(image_bytes).decode()
            
            # Use Google Custom Search API if available, otherwise construct search URL
            # For now, construct a Google Lens/Images search URL
            # In production, use Google Custom Search API with image parameter
            
            # Construct Google reverse image search URL
            search_url = f"https://www.google.com/searchbyimage?image_url={image_url}" if image_url else None
            
            return {
                "results": [],
                "provider": "google",
                "search_url": search_url,
                "note": "Google reverse image search - results require API integration",
                "image_size": len(image_bytes) if image_bytes else 0
            }
        
        except Exception as e:
            logger.error(f"Google image search failed: {e}")
            return {"error": str(e), "results": [], "provider": "google"}
    
    async def _search_tineye(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Search using TinEye API"""
        # TinEye API requires API key
        api_key = getattr(self.settings, 'tineye_api_key', None)
        
        if not api_key:
            # Fallback: Use TinEye web interface URL
            if image_url:
                search_url = f"https://tineye.com/search?url={image_url}"
                return {
                    "results": [],
                    "provider": "tineye",
                    "search_url": search_url,
                    "note": "TinEye API key not configured - manual search URL provided"
                }
            return {"error": "TinEye API key not configured", "results": []}
        
        try:
            # Download image if URL provided
            if image_url and not image_bytes:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_bytes = response.content
            
            if not image_bytes:
                return {"error": "Could not retrieve image", "results": []}
            
            # Use TinEye API
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"image": image_bytes}
                response = await client.post(
                    "https://api.tineye.com/rest/search/",
                    headers={"X-Tineye-Key": api_key},
                    files=files
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for match in data.get("results", []):
                    results.append({
                        "url": match.get("image_url", ""),
                        "title": match.get("domain", ""),
                        "score": match.get("score", 0),
                        "width": match.get("width"),
                        "height": match.get("height")
                    })
                
                return {
                    "results": results,
                    "provider": "tineye",
                    "count": len(results),
                    "total_results": data.get("total_results", 0)
                }
        
        except Exception as e:
            logger.error(f"TinEye search failed: {e}")
            return {"error": str(e), "results": [], "provider": "tineye"}
    
    async def _search_yandex(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Search using Yandex Images reverse search"""
        try:
            # Download image if URL provided
            if image_url and not image_bytes:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_bytes = response.content
            
            if not image_bytes:
                return {"error": "Could not retrieve image", "results": []}
            
            # Yandex reverse image search URL
            if image_url:
                search_url = f"https://yandex.com/images/search?url={image_url}&rpt=imageview"
                return {
                    "results": [],
                    "provider": "yandex",
                    "search_url": search_url,
                    "note": "Yandex reverse image search - results require web scraping"
                }
            
            return {
                "error": "Yandex search requires image URL",
                "results": []
            }
        
        except Exception as e:
            logger.error(f"Yandex search failed: {e}")
            return {"error": str(e), "results": [], "provider": "yandex"}
    
    async def find_similar_images(
        self,
        tiger_image_id: str,
        threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Find similar images online for a known tiger image
        
        Args:
            tiger_image_id: ID of tiger image in database
            threshold: Similarity threshold
            
        Returns:
            Similar images found online
        """
        try:
            from backend.database import get_db_session, TigerImage
            
            with get_db_session() as session:
                tiger_image = session.query(TigerImage).filter(
                    TigerImage.image_id == tiger_image_id
                ).first()
                
                if not tiger_image or not tiger_image.image_path:
                    return {"error": "Tiger image not found", "results": []}
                
                # Get image URL or path
                image_url = tiger_image.image_path
                if not image_url.startswith("http"):
                    # Local file - would need to upload or convert to URL
                    return {
                        "error": "Local image files require upload to search",
                        "results": []
                    }
                
                # Perform reverse search
                results = await self.reverse_search(image_url=image_url)
                
                return {
                    "tiger_image_id": tiger_image_id,
                    "search_results": results.get("results", []),
                    "provider": results.get("provider"),
                    "count": len(results.get("results", []))
                }
        
        except Exception as e:
            logger.error(f"Similar image search failed: {e}", exc_info=True)
            return {"error": str(e), "results": []}


# Singleton instance
_image_search_service: Optional[ImageSearchService] = None


def get_image_search_service() -> ImageSearchService:
    """Get global image search service instance (singleton)"""
    global _image_search_service
    if _image_search_service is None:
        _image_search_service = ImageSearchService()
    return _image_search_service

