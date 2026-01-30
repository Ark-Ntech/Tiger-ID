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
        provider: str = "all"
    ) -> Dict[str, Any]:
        """
        Perform reverse image search across multiple providers in parallel
        
        Args:
            image_url: URL of image to search
            image_bytes: Image bytes (alternative to image_url)
            provider: Search provider ("all" for parallel search, or specific provider)
            
        Returns:
            Search results dictionary with results from all providers
        """
        if not image_url and not image_bytes:
            return {"error": "Either image_url or image_bytes must be provided"}
        
        try:
            if provider == "all":
                # Run all searches in parallel
                return await self._search_all_providers(image_url, image_bytes)
            elif provider == "google":
                return await self._search_google_images(image_url, image_bytes)
            elif provider == "tineye":
                return await self._search_tineye(image_url, image_bytes)
            elif provider == "yandex":
                return await self._search_yandex(image_url, image_bytes)
            elif provider == "tavily":
                return await self._search_tavily(image_url, image_bytes)
            else:
                return await self._search_all_providers(image_url, image_bytes)
        except Exception as e:
            logger.error(f"Reverse image search failed: {e}", exc_info=True)
            return {"error": str(e), "results": []}
    
    async def _search_all_providers(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Run searches across all providers in parallel"""
        import asyncio
        
        logger.info("Running parallel reverse image search across all providers...")
        
        # Create tasks for all providers
        tasks = {
            "google": self._search_google_images(image_url, image_bytes),
            "tavily": self._search_tavily(image_url, image_bytes),
            "facilities": self._crawl_facility_websites()
        }
        
        # Run all in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Combine results
        combined = {}
        for provider, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"{provider} search failed: {result}")
                combined[provider] = {"error": str(result), "results": [], "count": 0}
            else:
                combined[provider] = result
        
        # Calculate totals
        total_results = sum(r.get("count", 0) for r in combined.values() if isinstance(r, dict))
        
        logger.info(f"Parallel search complete: {total_results} total results from {len(combined)} providers")
        
        return {
            "providers": combined,
            "total_results": total_results,
            "providers_searched": len([r for r in combined.values() if isinstance(r, dict) and r.get("count", 0) > 0])
        }
    
    async def _search_google_images(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Search using Google Images via SerpApi or Firecrawl fallback"""
        try:
            import os
            
            # Check for SerpApi key (note: SerpApi not Serper - different services!)
            serpapi_key = os.getenv("SERPER_API_KEY")  # Using SERPER_API_KEY env var
            firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
            
            if not serpapi_key and not firecrawl_key:
                logger.warning("No API keys configured for image search")
                search_url = f"https://www.google.com/searchbyimage?image_url={image_url}" if image_url else None
                return {
                    "results": [],
                    "provider": "google",
                    "search_url": search_url,
                    "note": "API keys not configured (Set SERPER_API_KEY for SerpApi or FIRECRAWL_API_KEY)",
                    "count": 0
                }
            
            # Download image if URL provided
            if image_url and not image_bytes:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_bytes = response.content
            
            if not image_bytes:
                return {"error": "Could not retrieve image", "results": []}
            
            # Try SerpApi first (if key available)
            if serpapi_key:
                try:
                    logger.info(f"Calling SerpApi for Google Lens search...")
                    
                    # Upload image to get a URL (SerpApi doesn't support base64 images directly for Google Lens)
                    # For now, use Google Reverse Image Search API
                    # Reference: https://serpapi.com/google-reverse-image-api
                    
                    # Encode image
                    image_b64 = base64.b64encode(image_bytes).decode()
                    
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        # SerpApi Google Lens endpoint
                        # Note: SerpApi doesn't support base64 data URLs in GET params (URL too long)
                        # We need a publicly accessible image URL for Google Lens
                        if image_url and image_url.startswith("http"):
                            params = {
                                "engine": "google_lens",
                                "url": image_url,
                                "api_key": serpapi_key
                            }
                            response = await client.get(
                                "https://serpapi.com/search",
                                params=params
                            )
                        else:
                            # For local images without URL, use Firecrawl or skip
                            logger.info("SerpApi requires public image URL - using Firecrawl instead")
                            if firecrawl_key:
                                return await self._search_firecrawl_images(image_url, image_bytes)
                            else:
                                return {
                                    "error": "SerpApi requires public image URL",
                                    "results": [],
                                    "provider": "google",
                                    "count": 0,
                                    "note": "Upload image to public URL or use Firecrawl for local images"
                                }
                        
                        if response.status_code != 200:
                            error_msg = response.text
                            logger.warning(f"SerpApi error: {response.status_code} - {error_msg}")
                            
                            # Try Firecrawl fallback if available
                            if firecrawl_key:
                                logger.info("Falling back to Firecrawl for image search...")
                                return await self._search_firecrawl_images(image_url, image_bytes)
                            
                            return {
                                "error": f"SerpApi: {response.status_code}",
                                "results": [],
                                "provider": "google",
                                "count": 0,
                                "note": f"SerpApi error. Check key at https://serpapi.com. Error: {error_msg[:100]}"
                            }
                        
                        data = response.json()
                        
                        # Parse SerpApi results
                        results = []
                        
                        # Google Lens results
                        if "visual_matches" in data:
                            for item in data.get("visual_matches", [])[:10]:
                                results.append({
                                    "url": item.get("link", ""),
                                    "source": item.get("source", ""),
                                    "title": item.get("title", ""),
                                    "thumbnail": item.get("thumbnail", "")
                                })
                        
                        # Reverse image results
                        elif "inline_images" in data:
                            for item in data.get("inline_images", [])[:10]:
                                results.append({
                                    "url": item.get("original", ""),
                                    "source": item.get("source", ""),
                                    "title": item.get("title", ""),
                                    "thumbnail": item.get("thumbnail", "")
                                })
                        
                        logger.info(f"SerpApi returned {len(results)} results")
                        
                        return {
                            "results": results,
                            "provider": "google",
                            "count": len(results),
                            "api_used": "serpapi"
                        }
                
                except Exception as e:
                    logger.error(f"SerpApi search failed: {e}")
                    # Try Firecrawl fallback
                    if firecrawl_key:
                        logger.info("Falling back to Firecrawl after SerpApi error...")
                        return await self._search_firecrawl_images(image_url, image_bytes)
                    raise
            
            # Use Firecrawl if SerpApi not available
            elif firecrawl_key:
                logger.info("Using Firecrawl for image search...")
                return await self._search_firecrawl_images(image_url, image_bytes)
            
            return {"error": "No API keys available", "results": []}
        
        except Exception as e:
            logger.error(f"Google image search failed: {e}")
            return {"error": str(e), "results": [], "provider": "google"}
    
    async def _search_firecrawl_images(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Search using Firecrawl as fallback"""
        try:
            import os
            
            firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
            
            if not firecrawl_key:
                return {"error": "Firecrawl API key not configured", "results": []}
            
            # Firecrawl doesn't have direct reverse image search
            # But we can use it to scrape Google's reverse image search page
            if not image_url:
                return {
                    "error": "Firecrawl requires image URL (not bytes)",
                    "results": [],
                    "note": "Upload image to get URL for Firecrawl search"
                }
            
            logger.info("Using Firecrawl to scrape Google reverse image search...")
            
            # Construct Google reverse image search URL
            search_url = f"https://www.google.com/searchbyimage?image_url={image_url}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v0/scrape",
                    headers={
                        "Authorization": f"Bearer {firecrawl_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": search_url,
                        "formats": ["markdown", "links"]
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Firecrawl error: {response.status_code} - {response.text}")
                    return {
                        "error": f"Firecrawl: {response.status_code}",
                        "results": [],
                        "provider": "google",
                        "count": 0
                    }
                
                data = response.json()
                
                # Extract links from scraped page
                results = []
                links = data.get("data", {}).get("links", [])
                
                for link in links[:10]:
                    if link.startswith("http") and "google.com" not in link:
                        results.append({
                            "url": link,
                            "source": "firecrawl_scrape",
                            "title": link
                        })
                
                logger.info(f"Firecrawl returned {len(results)} links from Google reverse search")
                
                return {
                    "results": results,
                    "provider": "google",
                    "count": len(results),
                    "api_used": "firecrawl",
                    "search_url": search_url
                }
        
        except Exception as e:
            logger.error(f"Firecrawl search failed: {e}")
            return {"error": str(e), "results": [], "provider": "firecrawl"}
    
    async def _search_tavily(
        self,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Search using Tavily API for tiger-related content"""
        try:
            import os
            
            tavily_key = os.getenv("TAVILY_API_KEY")
            
            if not tavily_key:
                logger.warning("Tavily API key not configured")
                return {
                    "error": "Tavily API key not configured",
                    "results": [],
                    "provider": "tavily",
                    "count": 0,
                    "note": "Set TAVILY_API_KEY environment variable"
                }
            
            logger.info("Searching Tavily for tiger-related content...")
            
            # Tavily is a research/search API - use it to search for tiger-related content
            # Extract context if we have bytes
            search_query = "tiger wildlife conservation facility"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    headers={"Content-Type": "application/json"},
                    json={
                        "api_key": tavily_key,
                        "query": search_query,
                        "search_depth": "advanced",
                        "include_images": True,
                        "max_results": 10
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Tavily API error: {response.status_code} - {response.text}")
                    return {
                        "error": f"Tavily: {response.status_code}",
                        "results": [],
                        "provider": "tavily",
                        "count": 0
                    }
                
                data = response.json()
                
                # Parse Tavily results
                results = []
                for item in data.get("results", []):
                    results.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "content": item.get("content", "")[:200],  # Truncate content
                        "score": item.get("score", 0)
                    })
                
                # Add images if available
                images = data.get("images", [])
                
                logger.info(f"Tavily returned {len(results)} results, {len(images)} images")
                
                return {
                    "results": results,
                    "images": images,
                    "provider": "tavily",
                    "count": len(results) + len(images),
                    "api_used": "tavily"
                }
        
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {"error": str(e), "results": [], "provider": "tavily", "count": 0}
    
    async def _crawl_facility_websites(self) -> Dict[str, Any]:
        """
        Crawl facility websites from database using Firecrawl.
        Searches for tiger-related content on known facility websites.
        """
        try:
            import os
            import asyncio
            from backend.database import get_db_session
            from backend.database.models import Facility
            
            firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
            
            if not firecrawl_key:
                return {
                    "error": "Firecrawl API key not configured",
                    "results": [],
                    "provider": "facilities",
                    "count": 0
                }
            
            logger.info("Crawling facility websites from database...")
            
            # Get facilities with websites
            db_gen = get_db_session()
            db = next(db_gen)
            
            try:
                facilities = db.query(Facility).filter(
                    Facility.website.isnot(None),
                    Facility.website != ""
                ).limit(10).all()  # Limit to 10 for performance
                
                if not facilities:
                    logger.info("No facility websites found in database")
                    return {
                        "results": [],
                        "provider": "facilities",
                        "count": 0,
                        "note": "No facility websites in database"
                    }
                
                logger.info(f"Found {len(facilities)} facilities with websites")
                
                # Crawl each facility in parallel (limited batch)
                async def crawl_facility(facility):
                    try:
                        url = facility.website
                        if not url.startswith("http"):
                            url = f"https://{url}"
                        
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.post(
                                "https://api.firecrawl.dev/v0/scrape",
                                headers={
                                    "Authorization": f"Bearer {firecrawl_key}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "url": url,
                                    "formats": ["markdown", "links"],
                                    "onlyMainContent": True
                                }
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                content = data.get("data", {}).get("markdown", "")
                                links = data.get("data", {}).get("links", [])
                                
                                # Check for tiger-related content
                                tiger_keywords = ['tiger', 'panthera', 'big cat', 'wildlife', 'conservation']
                                has_tiger_content = any(kw in content.lower() for kw in tiger_keywords)
                                
                                return {
                                    "facility": facility.exhibitor_name,
                                    "url": url,
                                    "has_tiger_content": has_tiger_content,
                                    "content_preview": content[:300],
                                    "links_found": len(links),
                                    "success": True
                                }
                            else:
                                return {
                                    "facility": facility.exhibitor_name,
                                    "url": url,
                                    "error": f"HTTP {response.status_code}",
                                    "success": False
                                }
                    
                    except Exception as e:
                        return {
                            "facility": facility.exhibitor_name if facility else "unknown",
                            "url": url if 'url' in locals() else "unknown",
                            "error": str(e),
                            "success": False
                        }
                
                # Crawl facilities in parallel (limit to 5 concurrent)
                crawl_tasks = [crawl_facility(f) for f in facilities[:5]]
                crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
                
                # Filter successful results
                successful = [r for r in crawl_results if isinstance(r, dict) and r.get("success")]
                
                logger.info(f"Crawled {len(successful)}/{len(facilities)} facilities successfully")
                
                return {
                    "results": crawl_results,
                    "provider": "facilities",
                    "count": len(successful),
                    "crawled": len(crawl_results),
                    "note": f"Crawled {len(successful)} facility websites"
                }
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Facility crawl failed: {e}")
            return {"error": str(e), "results": [], "provider": "facilities", "count": 0}
    
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

