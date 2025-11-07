"""News monitoring service for tracking tiger trafficking related news"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx

from backend.config.settings import get_settings
from backend.services.web_search_service import get_web_search_service
from backend.services.reference_data_service import ReferenceDataService
from backend.database import get_db_session
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class NewsMonitoringService:
    """Service for monitoring news articles about tiger trafficking"""
    
    def __init__(self):
        """Initialize news monitoring service"""
        self.settings = get_settings()
        self.web_search = get_web_search_service()
        
        # News search keywords
        self.keywords = [
            "tiger trafficking",
            "illegal tiger trade",
            "tiger seizure",
            "tiger rescue",
            "exotic animal trafficking",
            "tiger facility violation",
            "USDA tiger inspection",
            "tiger for sale"
        ]
    
    async def search_news(
        self,
        query: Optional[str] = None,
        days: int = 7,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for recent news articles
        
        Args:
            query: Custom search query (uses keywords if not provided)
            days: Number of days to search back
            limit: Maximum number of results
            
        Returns:
            News articles dictionary
        """
        try:
            # Construct search query
            if not query:
                # Use keywords with date range
                query = " OR ".join(self.keywords)
                date_filter = f" (after:{datetime.now().date() - timedelta(days=days)})"
                query += date_filter
            
            # Use web search service
            search_results = await self.web_search.search(
                query=query,
                limit=limit,
                provider="serper"  # Serper works well for news
            )
            
            # Filter and format news results
            articles = []
            for result in search_results.get("results", []):
                # Check if result looks like a news article
                if self._is_news_article(result):
                    articles.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", ""),
                        "date": result.get("date"),
                        "source": self._extract_source(result.get("url", ""))
                    })
            
            return {
                "articles": articles,
                "count": len(articles),
                "query": query,
                "search_date": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"News search failed: {e}", exc_info=True)
            return {"error": str(e), "articles": []}
    
    async def monitor_reference_facilities(
        self,
        days: int = 7,
        limit_per_facility: int = 5
    ) -> Dict[str, Any]:
        """
        Monitor news mentions of reference facilities
        
        Args:
            days: Number of days to search back
            limit_per_facility: Max results per facility
            
        Returns:
            News articles grouped by facility
        """
        try:
            session = next(get_db_session())
            try:
                ref_service = ReferenceDataService(session)
                reference_facilities = ref_service.get_reference_facilities(limit=100)
                
                facility_news = {}
                
                for facility in reference_facilities:
                    facility_name = facility.exhibitor_name
                    
                    # Search for news about this facility
                    query = f'"{facility_name}" tiger'
                    news_results = await self.search_news(
                        query=query,
                        days=days,
                        limit=limit_per_facility
                    )
                    
                    if news_results.get("articles"):
                        facility_news[facility_name] = {
                            "facility_id": str(facility.facility_id),
                            "articles": news_results["articles"],
                            "count": len(news_results["articles"])
                        }
                
                return {
                    "facility_news": facility_news,
                    "total_facilities_checked": len(reference_facilities),
                    "facilities_with_news": len(facility_news),
                    "search_date": datetime.utcnow().isoformat()
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Reference facility monitoring failed: {e}", exc_info=True)
            return {"error": str(e), "facility_news": {}}
    
    async def search_facility_news(
        self,
        facility_name: str,
        days: int = 30,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for news about a specific facility
        
        Args:
            facility_name: Name of facility
            days: Number of days to search back
            limit: Maximum number of results
            
        Returns:
            News articles about the facility
        """
        query = f'"{facility_name}" (tiger OR facility OR USDA OR violation OR inspection)'
        
        return await self.search_news(query=query, days=days, limit=limit)
    
    def _is_news_article(self, result: Dict[str, Any]) -> bool:
        """Check if search result looks like a news article"""
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        
        # News domain indicators
        news_domains = [
            "news", "article", "report", "press", "times", "post",
            "tribune", "herald", "chronicle", "journal", "gazette"
        ]
        
        # Check URL or title for news indicators
        for domain in news_domains:
            if domain in url or domain in title:
                return True
        
        # Check for common news TLDs
        news_tlds = [".com/news", ".org/news", ".net/news"]
        for tld in news_tlds:
            if tld in url:
                return True
        
        return False
    
    def _extract_source(self, url: str) -> str:
        """Extract news source from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Get main domain
            parts = domain.split(".")
            if len(parts) >= 2:
                return ".".join(parts[-2:])
            
            return domain
        except Exception:
            return "unknown"
    
    async def extract_article_content(self, url: str) -> Dict[str, Any]:
        """
        Extract full article content from URL
        
        Args:
            url: Article URL
            
        Returns:
            Extracted article content
        """
        try:
            from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
            
            firecrawl = FirecrawlMCPServer()
            scrape_result = await firecrawl._handle_scrape(url, extract=True)
            
            if "error" in scrape_result:
                return {"error": scrape_result.get("error"), "url": url}
            
            return {
                "url": url,
                "title": scrape_result.get("title", ""),
                "content": scrape_result.get("content", ""),
                "extracted": scrape_result.get("extracted", "")
            }
        
        except Exception as e:
            logger.error(f"Article extraction failed: {e}")
            return {"error": str(e), "url": url}


# Singleton instance
_news_service: Optional[NewsMonitoringService] = None


def get_news_monitoring_service() -> NewsMonitoringService:
    """Get global news monitoring service instance (singleton)"""
    global _news_service
    if _news_service is None:
        _news_service = NewsMonitoringService()
    return _news_service

