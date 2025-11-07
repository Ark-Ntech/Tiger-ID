"""Web search service with support for multiple providers"""

from typing import Dict, Any, List, Optional
import os
import json
import hashlib
import httpx
from datetime import datetime, timedelta

from backend.config.settings import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import optional dependencies
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - search caching disabled")


class WebSearchService:
    """Service for web search with multiple provider support"""
    
    def __init__(self):
        """Initialize web search service"""
        self.settings = get_settings()
        self.web_search_config = self.settings.web_search
        
        # Initialize Redis for caching if available
        self.redis_client = None
        if REDIS_AVAILABLE and self.web_search_config.enable_caching:
            try:
                import redis as redis_client
                self.redis_client = redis_client.from_url(
                    self.settings.redis.url,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed - caching disabled: {e}")
                self.redis_client = None
    
    def _get_cache_key(self, query: str, limit: int, provider: Optional[str] = None) -> str:
        """Generate cache key for search query"""
        key_parts = ["web_search", provider or self.web_search_config.provider, query, str(limit)]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search result"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any], ttl: int = None):
        """Cache search result"""
        if not self.redis_client:
            return
        
        try:
            ttl = ttl or self.web_search_config.cache_ttl_seconds
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search the web using configured provider
        
        Args:
            query: Search query
            limit: Maximum number of results
            provider: Search provider (firecrawl, serper, tavily, perplexity)
                     If None, uses configured default
            
        Returns:
            Search results dictionary
        """
        provider = provider or self.web_search_config.provider
        
        # Check cache first
        if self.web_search_config.enable_caching:
            cache_key = self._get_cache_key(query, limit, provider)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"Returning cached search result for query: {query[:50]}")
                return cached_result
        
        # Perform search based on provider
        try:
            if provider == "serper":
                result = await self._search_serper(query, limit)
            elif provider == "tavily":
                result = await self._search_tavily(query, limit)
            elif provider == "perplexity":
                result = await self._search_perplexity(query, limit)
            elif provider == "firecrawl":
                # Firecrawl doesn't have search API, use Google search via scrape
                result = await self._search_firecrawl_fallback(query, limit)
            else:
                # Default to Serper if available, otherwise fallback
                if self.web_search_config.serper_api_key:
                    result = await self._search_serper(query, limit)
                else:
                    result = await self._search_firecrawl_fallback(query, limit)
            
            # Cache result
            if self.web_search_config.enable_caching:
                cache_key = self._get_cache_key(query, limit, provider)
                self._cache_result(cache_key, result)
            
            return result
        
        except Exception as e:
            logger.error(f"Search failed with provider {provider}: {e}", exc_info=True)
            # Fallback to alternative provider
            if provider != "firecrawl":
                logger.info(f"Falling back to firecrawl search")
                try:
                    result = await self._search_firecrawl_fallback(query, limit)
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback search also failed: {fallback_error}")
            
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": str(e),
                "provider": provider
            }
    
    async def _search_serper(self, query: str, limit: int = 10, location: Optional[str] = None, gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
        """
        Search using Serper API (Google Search)
        
        Args:
            query: Search query
            limit: Maximum number of results (max 20)
            location: Geographic location for localized results (e.g., "Austin, Texas")
            gl: Country code (e.g., "us", "uk")
            hl: Language code (e.g., "en", "es")
        """
        api_key = self.web_search_config.serper_api_key
        if not api_key:
            raise ValueError("Serper API key not configured")
        
        # Build request payload with all available parameters
        payload = {
            "q": query,
            "num": min(limit, 20)  # Serper max is 20
        }
        
        # Add optional parameters
        if location:
            payload["location"] = location
        if gl:
            payload["gl"] = gl
        if hl:
            payload["hl"] = hl
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": api_key,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                # Check for 403 Forbidden - might be invalid API key or rate limit
                if response.status_code == 403:
                    error_text = response.text
                    logger.error(f"Serper API 403 Forbidden. Response: {error_text[:200]}")
                    raise ValueError(f"Serper API access denied (403). Check API key validity and account status. Response: {error_text[:200]}")
                
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    error_text = e.response.text if e.response else "Unknown error"
                    logger.error(f"Serper API 403 Forbidden. Response: {error_text[:200]}")
                    raise ValueError(f"Serper API access denied (403). Check API key validity and account status. Response: {error_text[:200]}")
                raise
            
            # Extract organic results
            results = []
            for item in data.get("organic", [])[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", 0),
                    "date": item.get("date", "")
                })
            
            # Extract additional result types
            answer_box = data.get("answerBox")
            knowledge_graph = data.get("knowledgeGraph")
            people_also_ask = data.get("peopleAlsoAsk", [])
            related_questions = data.get("relatedQuestions", [])
            
            return {
                "results": results,
                "query": query,
                "count": len(results),
                "provider": "serper",
                "total_results": data.get("searchInformation", {}).get("totalResults", "0"),
                # Include additional result types
                "answer_box": answer_box if answer_box else None,
                "knowledge_graph": knowledge_graph if knowledge_graph else None,
                "people_also_ask": people_also_ask[:5] if people_also_ask else [],  # Limit to 5
                "related_questions": related_questions[:5] if related_questions else []  # Limit to 5
            }
    
    async def _search_tavily(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search using Tavily API (AI-powered search)"""
        api_key = self.web_search_config.tavily_api_key
        if not api_key:
            raise ValueError("Tavily API key not configured")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": min(limit, 20),  # Tavily max is typically 20
                    "include_answer": False,
                    "include_raw_content": False
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", [])[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "score": item.get("score", 0.0),
                    "published_date": item.get("published_date")
                })
            
            return {
                "results": results,
                "query": query,
                "count": len(results),
                "provider": "tavily"
            }
    
    async def _search_perplexity(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search using Perplexity API (LLM-powered search)"""
        api_key = self.web_search_config.perplexity_api_key
        if not api_key:
            raise ValueError("Perplexity API key not configured")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "max_tokens": 1000,
                    "return_citations": True,
                    "search_domain_filter": [],
                    "return_images": False,
                    "return_related_questions": False
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract citations as results
            citations = data.get("citations", [])
            message = data.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
            
            results = []
            for idx, citation in enumerate(citations[:limit]):
                results.append({
                    "title": citation.get("title", ""),
                    "url": citation.get("url", ""),
                    "snippet": citation.get("text", ""),
                    "position": idx + 1
                })
            
            return {
                "results": results,
                "query": query,
                "count": len(results),
                "provider": "perplexity",
                "answer": content[:500] if content else None  # Include LLM answer
            }
    
    async def _search_firecrawl_fallback(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fallback search using Firecrawl to scrape Google search results page
        This is a workaround since Firecrawl doesn't have a search API
        """
        # Construct Google search URL
        search_url = f"https://www.google.com/search?q={query}&num={limit}"
        
        try:
            # Use Firecrawl to scrape the search results page
            from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
            
            firecrawl = FirecrawlMCPServer()
            scrape_result = await firecrawl._handle_scrape(search_url, extract=False)
            
            # Parse search results from HTML (simplified)
            # In production, you'd want more robust HTML parsing
            content = scrape_result.get("content", "")
            
            # For now, return a basic structure
            # Note: This is a placeholder - proper implementation would parse Google SERP HTML
            results = []
            
            # Try to extract URLs and titles from the content
            # This is a simplified approach - in production, use proper HTML parsing
            import re
            url_pattern = r'https?://[^\s<>"]+'
            urls = re.findall(url_pattern, content)
            
            for idx, url in enumerate(urls[:limit]):
                # Clean URL
                url = url.rstrip('.,;:!?)')
                if not url.startswith('http'):
                    continue
                
                results.append({
                    "title": f"Result {idx + 1}",
                    "url": url,
                    "snippet": f"Found via Google search",
                    "position": idx + 1
                })
            
            return {
                "results": results,
                "query": query,
                "count": len(results),
                "provider": "firecrawl_fallback",
                "note": "Results extracted from Google SERP via Firecrawl"
            }
        
        except Exception as e:
            logger.error(f"Firecrawl fallback search failed: {e}")
            # Return empty results if fallback fails
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": str(e),
                "provider": "firecrawl_fallback"
            }


# Singleton instance
_search_service: Optional[WebSearchService] = None


def get_web_search_service() -> WebSearchService:
    """Get global web search service instance (singleton)"""
    global _search_service
    if _search_service is None:
        _search_service = WebSearchService()
    return _search_service

