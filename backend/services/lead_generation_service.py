"""Automated lead generation service for suspicious activity detection"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from backend.services.web_search_service import get_web_search_service
from backend.services.data_extraction_service import DataExtractionService
from backend.services.reference_data_service import ReferenceDataService
from backend.services.reference_data_service import ReferenceDataService
from backend.database import get_db_session, Facility
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class LeadGenerationService:
    """Service for generating investigation leads from web discoveries"""
    
    def __init__(self):
        """Initialize lead generation service"""
        self.web_search = get_web_search_service()
        self.data_extraction = DataExtractionService()
    
    async def search_suspicious_listings(
        self,
        location: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for suspicious tiger listings (for sale, adoption, etc.)
        
        Args:
            location: Geographic location to filter by
            limit: Maximum number of results
            
        Returns:
            Listings found
        """
        queries = [
            'tiger for sale',
            'tiger cub for sale',
            'tiger adoption',
            'tiger rescue for sale',
            'exotic tiger',
            'tiger available'
        ]
        
        if location:
            queries = [f'{q} {location}' for q in queries]
        
        all_listings = []
        
        for query in queries:
            try:
                search_results = await self.web_search.search(query, limit=10)
                
                for result in search_results.get("results", []):
                    # Score listing for suspiciousness
                    score = self._score_listing_suspiciousness(result)
                    
                    if score > 0.5:  # Threshold for suspicious
                        all_listings.append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "snippet": result.get("snippet", ""),
                            "suspicious_score": score,
                            "query": query,
                            "location": location
                        })
            except Exception as e:
                logger.error(f"Listing search failed for query '{query}': {e}")
        
        # Remove duplicates and sort by score
        unique_listings = self._deduplicate_listings(all_listings)
        unique_listings.sort(key=lambda x: x["suspicious_score"], reverse=True)
        
        return {
            "listings": unique_listings[:limit],
            "count": len(unique_listings),
            "location": location
        }
    
    async def match_listings_to_facilities(
        self,
        listings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match suspicious listings to known facilities
        
        Args:
            listings: List of listings to match
            
        Returns:
            Matched listings with facility information
        """
        with get_db_session() as session:
            ref_service = ReferenceDataService(session)
            
            matched = []
            
            for listing in listings:
                listing_url = listing.get("url", "")
                listing_title = listing.get("title", "")
                listing_snippet = listing.get("snippet", "")
                
                # Extract data from listing page
                try:
                    extracted = await self.data_extraction.extract_listing_data(listing_url)
                    extracted_data = extracted.get("extracted", {})
                    
                    # Try to match to reference facilities
                    location = extracted_data.get("location", {})
                    facility_matches = ref_service.find_matching_facilities(
                        state=location.get("state"),
                        city=location.get("city"),
                        name=extracted_data.get("title")
                    )
                    
                    if facility_matches:
                        # Boost suspicious score if matches reference facility
                        listing["suspicious_score"] = min(1.0, listing["suspicious_score"] + 0.3)
                        listing["matched_facilities"] = [
                            {
                                "facility_id": str(f.facility_id),
                                "exhibitor_name": f.exhibitor_name,
                                "state": f.state
                            }
                            for f in facility_matches
                        ]
                    
                    listing["extracted_data"] = extracted_data
                    
                except Exception as e:
                    logger.warning(f"Failed to extract/match listing {listing_url}: {e}")
                
                matched.append(listing)
            
            return {
                "listings": matched,
                "count": len(matched),
                "matched_count": sum(1 for l in matched if l.get("matched_facilities"))
            }
    
    async def search_social_media_suspicious_posts(
        self,
        keywords: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search social media for suspicious posts showing tigers
        
        Args:
            keywords: Additional keywords to search for
            limit: Maximum number of results
            
        Returns:
            Suspicious posts found
        """
        if not keywords:
            keywords = ["tiger", "tiger cub", "pet tiger", "private tiger"]
        
        all_posts = []
        
        for keyword in keywords:
            queries = [
                f'{keyword} facebook',
                f'{keyword} instagram',
                f'{keyword} private owner'
            ]
            
            for query in queries:
                try:
                    search_results = await self.web_search.search(query, limit=10)
                    
                    for result in search_results.get("results", []):
                        url = result.get("url", "")
                        snippet = result.get("snippet", "")
                        
                        # Check if it's a social media post
                        if any(domain in url.lower() for domain in ["facebook.com", "instagram.com", "twitter.com"]):
                            score = self._score_post_suspiciousness(result)
                            
                            if score > 0.5:
                                all_posts.append({
                                    "url": url,
                                    "title": result.get("title", ""),
                                    "snippet": snippet,
                                    "suspicious_score": score,
                                    "platform": self._extract_platform(url),
                                    "keyword": keyword
                                })
                
                except Exception as e:
                    logger.error(f"Social media search failed: {e}")
        
        # Remove duplicates
        unique_posts = self._deduplicate_posts(all_posts)
        unique_posts.sort(key=lambda x: x["suspicious_score"], reverse=True)
        
        return {
            "posts": unique_posts[:limit],
            "count": len(unique_posts)
        }
    
    async def generate_leads(
        self,
        location: Optional[str] = None,
        include_listings: bool = True,
        include_social_media: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive investigation leads
        
        Args:
            location: Geographic location filter
            include_listings: Include marketplace listings
            include_social_media: Include social media posts
            
        Returns:
            Generated leads
        """
        leads = {
            "listings": [],
            "social_media_posts": [],
            "generated_at": datetime.utcnow().isoformat(),
            "location": location
        }
        
        if include_listings:
            listings = await self.search_suspicious_listings(location=location)
            matched_listings = await self.match_listings_to_facilities(
                listings.get("listings", [])
            )
            leads["listings"] = matched_listings.get("listings", [])
        
        if include_social_media:
            posts = await self.search_social_media_suspicious_posts()
            leads["social_media_posts"] = posts.get("posts", [])
        
        # Calculate overall lead scores
        all_leads = leads["listings"] + leads["social_media_posts"]
        high_priority_leads = [lead for lead in all_leads if lead.get("suspicious_score", 0) > 0.7]
        
        return {
            **leads,
            "total_leads": len(all_leads),
            "high_priority_leads": len(high_priority_leads),
            "summary": {
                "listings_count": len(leads["listings"]),
                "posts_count": len(leads["social_media_posts"]),
                "matched_to_facilities": sum(1 for l in leads["listings"] if l.get("matched_facilities"))
            }
        }
    
    def _score_listing_suspiciousness(self, result: Dict[str, Any]) -> float:
        """Score how suspicious a listing appears"""
        score = 0.0
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        url = result.get("url", "").lower()
        
        text = f"{title} {snippet}"
        
        # Suspicious indicators
        suspicious_terms = [
            "for sale", "private sale", "cash only", "no questions",
            "urgent", "must sell", "no papers", "unregistered",
            "rescued", "adoption fee", "rehoming"
        ]
        
        for term in suspicious_terms:
            if term in text:
                score += 0.1
        
        # Check for price mentions (often suspicious)
        import re
        price_patterns = [r'\$[\d,]+', r'\d+\s*(?:dollars|dollar)']
        if any(re.search(pattern, text) for pattern in price_patterns):
            score += 0.2
        
        # Boost if mentions location without proper facility
        if any(word in text for word in ["private", "home", "backyard"]):
            score += 0.15
        
        return min(1.0, score)
    
    def _score_post_suspiciousness(self, result: Dict[str, Any]) -> float:
        """Score how suspicious a social media post appears"""
        score = 0.0
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        text = f"{title} {snippet}"
        
        # Suspicious indicators for social media
        suspicious_terms = [
            "pet tiger", "private tiger", "my tiger", "our tiger",
            "backyard tiger", "home tiger", "petting tiger"
        ]
        
        for term in suspicious_terms:
            if term in text:
                score += 0.2
        
        # Location without facility context is suspicious
        if any(word in text for word in ["home", "house", "backyard", "private"]):
            score += 0.15
        
        return min(1.0, score)
    
    def _deduplicate_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate listings"""
        seen_urls = set()
        unique = []
        
        for listing in listings:
            url = listing.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(listing)
        
        return unique
    
    def _deduplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts"""
        seen_urls = set()
        unique = []
        
        for post in posts:
            url = post.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(post)
        
        return unique
    
    def _extract_platform(self, url: str) -> str:
        """Extract social media platform from URL"""
        url_lower = url.lower()
        
        if "facebook" in url_lower:
            return "facebook"
        elif "instagram" in url_lower:
            return "instagram"
        elif "twitter" in url_lower or "x.com" in url_lower:
            return "twitter"
        else:
            return "unknown"


# Singleton instance
_lead_service: Optional[LeadGenerationService] = None


def get_lead_generation_service() -> LeadGenerationService:
    """Get global lead generation service instance (singleton)"""
    global _lead_service
    if _lead_service is None:
        _lead_service = LeadGenerationService()
    return _lead_service

