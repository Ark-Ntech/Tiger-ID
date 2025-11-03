"""Advanced data extraction service for structured data from web sources"""

from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime

from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class DataExtractionService:
    """Service for extracting structured data from web sources"""
    
    def __init__(self):
        """Initialize data extraction service"""
        self.firecrawl = FirecrawlMCPServer()
    
    async def extract_facility_data(self, url: str) -> Dict[str, Any]:
        """
        Extract facility information from a webpage
        
        Args:
            url: URL to extract from
            
        Returns:
            Extracted facility data
        """
        schema = {
            "type": "object",
            "properties": {
                "facility_name": {
                    "type": "string",
                    "description": "Name of the facility or exhibitor"
                },
                "usda_license": {
                    "type": "string",
                    "description": "USDA license number if mentioned"
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "state": {"type": "string"},
                        "city": {"type": "string"},
                        "address": {"type": "string"}
                    }
                },
                "tiger_count": {
                    "type": "integer",
                    "description": "Number of tigers if mentioned"
                },
                "contact_info": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string"},
                        "email": {"type": "string"},
                        "website": {"type": "string"}
                    }
                },
                "social_media": {
                    "type": "object",
                    "description": "Social media links (Facebook, Instagram, etc.)"
                }
            }
        }
        
        return await self.extract_structured_data(url, schema)
    
    async def extract_social_media_post(self, url: str) -> Dict[str, Any]:
        """
        Extract social media post metadata
        
        Args:
            url: Social media post URL
            
        Returns:
            Extracted post data
        """
        schema = {
            "type": "object",
            "properties": {
                "author": {
                    "type": "string",
                    "description": "Post author or account name"
                },
                "content": {
                    "type": "string",
                    "description": "Post text content"
                },
                "posted_at": {
                    "type": "string",
                    "description": "Post date/time if available"
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Image URLs in the post"
                },
                "engagement": {
                    "type": "object",
                    "properties": {
                        "likes": {"type": "integer"},
                        "comments": {"type": "integer"},
                        "shares": {"type": "integer"}
                    }
                }
            }
        }
        
        return await self.extract_structured_data(url, schema)
    
    async def extract_listing_data(self, url: str) -> Dict[str, Any]:
        """
        Extract listing data (e.g., for-sale, adoption, etc.)
        
        Args:
            url: Listing URL
            
        Returns:
            Extracted listing data
        """
        schema = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Listing title"
                },
                "description": {
                    "type": "string",
                    "description": "Listing description"
                },
                "price": {
                    "type": "string",
                    "description": "Price if mentioned"
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "state": {"type": "string"},
                        "city": {"type": "string"}
                    }
                },
                "contact_info": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string"},
                        "email": {"type": "string"}
                    }
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Image URLs"
                },
                "posted_date": {
                    "type": "string",
                    "description": "Listing post date"
                }
            }
        }
        
        return await self.extract_structured_data(url, schema)
    
    async def extract_event_data(self, url: str) -> Dict[str, Any]:
        """
        Extract event information (dates, locations, etc.)
        
        Args:
            url: Event URL
            
        Returns:
            Extracted event data
        """
        schema = {
            "type": "object",
            "properties": {
                "event_name": {
                    "type": "string",
                    "description": "Name of the event"
                },
                "event_date": {
                    "type": "string",
                    "description": "Event date"
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "venue": {"type": "string"},
                        "address": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"}
                    }
                },
                "description": {
                    "type": "string",
                    "description": "Event description"
                }
            }
        }
        
        return await self.extract_structured_data(url, schema)
    
    async def extract_structured_data(
        self,
        url: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from a URL using Firecrawl
        
        Args:
            url: URL to extract from
            schema: JSON schema for extraction (optional)
            
        Returns:
            Extracted data dictionary
        """
        try:
            # Use Firecrawl extract if available
            result = await self.firecrawl._handle_extract(url, schema)
            
            if "error" in result:
                logger.warning(f"Extraction error: {result.get('error')}")
                # Fallback to scrape and manual extraction
                return await self._extract_from_scraped_content(url, schema)
            
            return {
                "url": url,
                "extracted": result.get("extracted", {}),
                "schema": schema,
                "extraction_method": "firecrawl_llm"
            }
        
        except Exception as e:
            logger.error(f"Extraction failed for {url}: {e}", exc_info=True)
            # Fallback to manual extraction
            return await self._extract_from_scraped_content(url, schema)
    
    async def _extract_from_scraped_content(
        self,
        url: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fallback: Extract data from scraped content using pattern matching"""
        try:
            # Scrape the page
            scrape_result = await self.firecrawl._handle_scrape(url, extract=False)
            content = scrape_result.get("content", "")
            html = scrape_result.get("html", "")
            
            extracted = {}
            
            if schema:
                # Try to extract based on schema properties
                properties = schema.get("properties", {})
                
                # Extract facility name
                if "facility_name" in properties:
                    extracted["facility_name"] = self._extract_facility_name(content)
                
                # Extract USDA license
                if "usda_license" in properties:
                    extracted["usda_license"] = self._extract_usda_license(content)
                
                # Extract location
                if "location" in properties:
                    extracted["location"] = self._extract_location(content)
                
                # Extract contact info
                if "contact_info" in properties:
                    extracted["contact_info"] = self._extract_contact_info(content, html)
                
                # Extract social media links
                if "social_media" in properties:
                    extracted["social_media"] = self._extract_social_media_links(content, html)
                
                # Extract images
                if "images" in properties:
                    extracted["images"] = self._extract_images(html)
                
                # Extract dates
                if "event_date" in properties or "posted_date" in properties:
                    extracted["dates"] = self._extract_dates(content)
            
            return {
                "url": url,
                "extracted": extracted,
                "schema": schema,
                "extraction_method": "pattern_matching"
            }
        
        except Exception as e:
            logger.error(f"Manual extraction failed: {e}")
            return {
                "url": url,
                "extracted": {},
                "error": str(e),
                "extraction_method": "failed"
            }
    
    def _extract_facility_name(self, content: str) -> Optional[str]:
        """Extract facility name from content"""
        # Look for common patterns
        patterns = [
            r"(?:Facility|Exhibitor|Organization):\s*([A-Z][^<\n]+)",
            r"(?:Name|Facility Name):\s*([A-Z][^<\n]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_usda_license(self, content: str) -> Optional[str]:
        """Extract USDA license number from content"""
        patterns = [
            r"USDA\s*(?:License|Lic\.|#)?:?\s*([A-Z0-9\-]+)",
            r"(?:License|Lic\.|Lic#)\s*(?:Number|#)?:?\s*([A-Z0-9\-]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_location(self, content: str) -> Dict[str, Optional[str]]:
        """Extract location information"""
        location = {}
        
        # Extract state (US states)
        state_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:State|ST)\b"
        state_match = re.search(state_pattern, content)
        if not state_match:
            # Try common state abbreviations
            state_abbrev_pattern = r"\b([A-Z]{2})\s+(?:State|ST|US)\b"
            state_match = re.search(state_abbrev_pattern, content)
        
        if state_match:
            location["state"] = state_match.group(1)
        
        # Extract city
        city_pattern = r"(?:City|Location):\s*([A-Z][^,\n<]+)"
        city_match = re.search(city_pattern, content, re.IGNORECASE)
        if city_match:
            location["city"] = city_match.group(1).strip()
        
        return location
    
    def _extract_contact_info(self, content: str, html: str) -> Dict[str, Optional[str]]:
        """Extract contact information"""
        contact = {}
        
        # Extract email
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        email_match = re.search(email_pattern, content)
        if email_match:
            contact["email"] = email_match.group(0)
        
        # Extract phone
        phone_patterns = [
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, content)
            if phone_match:
                contact["phone"] = phone_match.group(0)
                break
        
        # Extract website
        url_pattern = r"https?://[^\s<>\"']+"
        url_match = re.search(url_pattern, content)
        if url_match:
            url = url_match.group(0)
            if "facebook" not in url.lower() and "instagram" not in url.lower():
                contact["website"] = url
        
        return contact
    
    def _extract_social_media_links(self, content: str, html: str) -> Dict[str, str]:
        """Extract social media links"""
        social_media = {}
        
        # Extract Facebook
        fb_pattern = r"(?:facebook|fb)\.com/([^\s<>\"']+)"
        fb_match = re.search(fb_pattern, content, re.IGNORECASE)
        if fb_match:
            social_media["facebook"] = f"https://facebook.com/{fb_match.group(1)}"
        
        # Extract Instagram
        ig_pattern = r"instagram\.com/([^\s<>\"']+)"
        ig_match = re.search(ig_pattern, content, re.IGNORECASE)
        if ig_match:
            social_media["instagram"] = f"https://instagram.com/{ig_match.group(1)}"
        
        # Extract Twitter/X
        twitter_pattern = r"(?:twitter|x)\.com/([^\s<>\"']+)"
        twitter_match = re.search(twitter_pattern, content, re.IGNORECASE)
        if twitter_match:
            social_media["twitter"] = f"https://twitter.com/{twitter_match.group(1)}"
        
        # Extract YouTube
        yt_pattern = r"youtube\.com/(?:channel/|user/|@)?([^\s<>\"']+)"
        yt_match = re.search(yt_pattern, content, re.IGNORECASE)
        if yt_match:
            social_media["youtube"] = f"https://youtube.com/{yt_match.group(1)}"
        
        return social_media
    
    def _extract_images(self, html: str) -> List[str]:
        """Extract image URLs from HTML"""
        images = []
        
        # Extract img src attributes
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        img_matches = re.findall(img_pattern, html, re.IGNORECASE)
        
        for img_url in img_matches:
            if img_url.startswith("http"):
                images.append(img_url)
            elif img_url.startswith("/"):
                # Relative URL - would need base URL to resolve
                images.append(img_url)
        
        return images[:10]  # Limit to 10 images
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from content"""
        dates = []
        
        # Common date patterns
        date_patterns = [
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)
        
        return dates[:5]  # Limit to 5 dates

