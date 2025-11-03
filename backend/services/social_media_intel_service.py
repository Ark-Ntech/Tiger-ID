"""Social media intelligence service for deep profile analysis"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from backend.services.data_extraction_service import DataExtractionService
from backend.services.reference_data_service import ReferenceDataService
from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
from backend.database import get_db_session, Facility, Evidence
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class SocialMediaIntelService:
    """Service for social media intelligence gathering"""
    
    def __init__(self):
        """Initialize social media intelligence service"""
        self.firecrawl = FirecrawlMCPServer()
        self.data_extraction = DataExtractionService()
    
    async def analyze_profile(
        self,
        profile_url: str,
        facility_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Analyze a social media profile
        
        Args:
            profile_url: URL of social media profile
            facility_id: Optional facility ID to link analysis to
            
        Returns:
            Profile analysis results
        """
        try:
            # Crawl the profile
            crawl_result = await self.firecrawl._handle_crawl(
                url=profile_url,
                limit=50  # Get more pages for profile analysis
            )
            
            if "error" in crawl_result:
                return {"error": crawl_result.get("error"), "url": profile_url}
            
            pages = crawl_result.get("pages", [])
            
            # Extract profile information
            profile_data = await self.data_extraction.extract_social_media_post(profile_url)
            
            # Analyze posts for tiger-related content
            tiger_mentions = []
            images_found = []
            
            for page in pages:
                content = page.get("content", "").lower()
                
                # Check for tiger-related keywords
                if any(keyword in content for keyword in ["tiger", "exotic", "big cat"]):
                    tiger_mentions.append({
                        "url": page.get("url", ""),
                        "title": page.get("title", ""),
                        "snippet": content[:200]
                    })
                
                # Extract images
                extracted_images = profile_data.get("extracted", {}).get("images", [])
                images_found.extend(extracted_images)
            
            # Build engagement metrics
            engagement = {
                "total_posts": len(pages),
                "tiger_mentions": len(tiger_mentions),
                "images_found": len(images_found),
                "last_activity": datetime.utcnow().isoformat()
            }
            
            return {
                "profile_url": profile_url,
                "profile_data": profile_data.get("extracted", {}),
                "tiger_mentions": tiger_mentions[:10],  # Limit to 10
                "images_found": images_found[:20],  # Limit to 20
                "engagement": engagement,
                "facility_id": str(facility_id) if facility_id else None,
                "analysis_date": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Profile analysis failed: {e}", exc_info=True)
            return {"error": str(e), "url": profile_url}
    
    async def monitor_account(
        self,
        profile_url: str,
        facility_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Monitor a social media account for new posts
        
        Args:
            profile_url: URL of social media profile
            facility_id: Optional facility ID
            
        Returns:
            New posts found since last check
        """
        try:
            # Get previous analysis (would need to store in database)
            # For now, just analyze current state
            analysis = await self.analyze_profile(profile_url, facility_id)
            
            return {
                "profile_url": profile_url,
                "new_posts": analysis.get("tiger_mentions", []),
                "new_images": analysis.get("images_found", []),
                "last_check": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Account monitoring failed: {e}", exc_info=True)
            return {"error": str(e), "url": profile_url}
    
    def identify_connections(
        self,
        profile_urls: List[str]
    ) -> Dict[str, Any]:
        """
        Identify connections between social media accounts
        
        Args:
            profile_urls: List of profile URLs to analyze
            
        Returns:
            Connection analysis
        """
        # Extract domains and usernames
        connections = {
            "shared_content": [],
            "mutual_mentions": [],
            "platforms": {}
        }
        
        for url in profile_urls:
            # Extract platform
            platform = self._extract_platform(url)
            if platform:
                if platform not in connections["platforms"]:
                    connections["platforms"][platform] = []
                connections["platforms"][platform].append(url)
        
        return {
            "connections": connections,
            "total_profiles": len(profile_urls),
            "platforms": list(connections["platforms"].keys())
        }
    
    def _extract_platform(self, url: str) -> Optional[str]:
        """Extract social media platform from URL"""
        url_lower = url.lower()
        
        if "facebook" in url_lower:
            return "facebook"
        elif "instagram" in url_lower:
            return "instagram"
        elif "twitter" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "youtube" in url_lower:
            return "youtube"
        else:
            return None


# Singleton instance
_social_intel_service: Optional[SocialMediaIntelService] = None


def get_social_media_intel_service() -> SocialMediaIntelService:
    """Get global social media intelligence service instance (singleton)"""
    global _social_intel_service
    if _social_intel_service is None:
        _social_intel_service = SocialMediaIntelService()
    return _social_intel_service

