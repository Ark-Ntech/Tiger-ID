"""Background job for facility social media crawling with image extraction and analysis"""

import asyncio
from celery import shared_task
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4
import re
import httpx
from pathlib import Path

from backend.database import get_db_session, Facility, CrawlHistory, Evidence, Investigation
from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
from backend.services.data_extraction_service import DataExtractionService
from backend.services.reference_data_service import ReferenceDataService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


async def extract_images_from_content(content: str, html: str, base_url: str) -> List[str]:
    """Extract image URLs from scraped content"""
    images = []
    
    # Extract img src attributes from HTML
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    img_matches = re.findall(img_pattern, html, re.IGNORECASE)
    
    for img_url in img_matches:
        # Resolve relative URLs
        if img_url.startswith("http"):
            images.append(img_url)
        elif img_url.startswith("//"):
            images.append(f"https:{img_url}")
        elif img_url.startswith("/"):
            # Extract base domain from base_url
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            images.append(f"{base_domain}{img_url}")
        elif img_url:
            images.append(img_url)
    
    # Also look for image URLs in content (for markdown or plain text)
    url_pattern = r'https?://[^\s<>"\']+\.(?:jpg|jpeg|png|gif|webp|bmp)'
    url_matches = re.findall(url_pattern, content, re.IGNORECASE)
    images.extend(url_matches)
    
    # Remove duplicates and filter valid image URLs
    unique_images = []
    seen = set()
    for img in images:
        img_lower = img.lower()
        if img_lower not in seen and any(img_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
            unique_images.append(img)
            seen.add(img_lower)
    
    return unique_images[:50]  # Limit to 50 images per page


async def detect_tigers_in_image(image_url: str) -> Dict[str, Any]:
    """Detect tigers in an image using the detection model"""
    try:
        # Import detection model
        from backend.models.detection import TigerDetectionModel
        
        detection_model = TigerDetectionModel()
        
        # Download image
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content
        
        # Detect tigers
        detection_result = await detection_model.detect(image_bytes)
        
        return {
            "detected": bool(detection_result.get("detections")),
            "detections": detection_result.get("detections", []),
            "confidence": detection_result.get("confidence", 0.0) if detection_result.get("detections") else 0.0
        }
    except Exception as e:
        logger.warning(f"Tiger detection failed for {image_url}: {e}")
        return {
            "detected": False,
            "detections": [],
            "confidence": 0.0,
            "error": str(e)
        }


async def identify_tiger_from_image(image_url: str, image_bytes: bytes = None) -> Dict[str, Any]:
    """Identify tiger from image using re-identification model"""
    try:
        from backend.models.reid import TigerReIDModel
        from backend.database import get_db_session
        from backend.database.vector_search import find_matching_tigers
        
        if not image_bytes:
            # Download image if not provided
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_bytes = response.content
        
        # Generate embedding
        reid_model = TigerReIDModel()
        embedding = await reid_model.generate_embedding_from_bytes(image_bytes)
        
        # Search for matching tigers
        with get_db_session() as session:
            matches = find_matching_tigers(
                session,
                query_embedding=embedding,
                limit=5,
                similarity_threshold=0.8
            )
        
        return {
            "identified": len(matches) > 0,
            "matches": matches,
            "best_match": matches[0] if matches else None
        }
    except Exception as e:
        logger.warning(f"Tiger identification failed for {image_url}: {e}")
        return {
            "identified": False,
            "matches": [],
            "error": str(e)
        }


async def process_crawled_images(
    images: List[str],
    facility_id: str,
    source_url: str,
    session,
    is_reference_facility: bool = False
) -> Dict[str, Any]:
    """Process images from crawled pages"""
    images_found = len(images)
    tigers_detected = 0
    tigers_identified = 0
    evidence_created = 0
    
    for image_url in images[:20]:  # Limit processing to 20 images per crawl
        try:
            # Detect tigers in image
            detection_result = await detect_tigers_in_image(image_url)
            
            if detection_result.get("detected"):
                tigers_detected += 1
                
                # Download image for identification
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_bytes = response.content
                
                # Identify tiger
                identification_result = await identify_tiger_from_image(image_url, image_bytes)
                
                if identification_result.get("identified"):
                    tigers_identified += 1
                
                # Create evidence record (if investigation exists or create generic)
                # For now, create evidence linked to facility
                evidence_priority = "high" if is_reference_facility else "medium"
                
                evidence = Evidence(
                    investigation_id=uuid4(),  # TODO: Link to actual investigation or create facility investigation
                    source_type="web_search",
                    source_url=image_url,
                    content={
                        "image_url": image_url,
                        "detection_result": detection_result,
                        "identification_result": identification_result,
                        "facility_id": str(facility_id),
                        "source_url": source_url
                    },
                    extracted_text=f"Tiger image found on {source_url}",
                    relevance_score=0.9 if is_reference_facility else 0.7
                )
                session.add(evidence)
                evidence_created += 1
                
                logger.info(
                    f"Tiger detected/identified in image from {source_url}",
                    image_url=image_url[:100],
                    identified=identification_result.get("identified")
                )
        
        except Exception as e:
            logger.error(f"Error processing image {image_url}: {e}")
    
    session.commit()
    
    return {
        "images_found": images_found,
        "tigers_detected": tigers_detected,
        "tigers_identified": tigers_identified,
        "evidence_created": evidence_created
    }


@shared_task(name="crawl_facility_social_media")
def crawl_facility_social_media(facility_id: str) -> Dict[str, Any]:
    """Crawl social media for a facility to find new tiger images"""
    logger.info("Starting facility crawl", facility_id=facility_id)
    
    # Run async function
    return asyncio.run(_crawl_facility_async(facility_id))


async def _crawl_facility_async(facility_id: str) -> Dict[str, Any]:
    """Async implementation of facility crawl"""
    start_time = datetime.utcnow()
    
    with get_db_session() as session:
        facility = session.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        
        if not facility:
            return {"error": "Facility not found"}
        
        # Check if this is a reference facility
        is_reference = facility.is_reference_facility or False
        
        # Initialize services
        firecrawl = FirecrawlMCPServer()
        data_extraction = DataExtractionService()
        
        # Get social media links and website
        sources_to_crawl = {}
        if facility.social_media_links:
            sources_to_crawl.update(facility.social_media_links)
        if facility.website:
            sources_to_crawl["website"] = facility.website
        
        total_images_found = 0
        total_tigers_detected = 0
        total_tigers_identified = 0
        total_evidence_created = 0
        pages_crawled = 0
        errors = []
        
        # Crawl each source
        for platform, url in sources_to_crawl.items():
            try:
                logger.info(f"Crawling {platform}", url=url)
                
                # Scrape the page
                scrape_result = await firecrawl._handle_scrape(url, extract=False)
                
                if "error" in scrape_result:
                    errors.append(f"{platform}: {scrape_result.get('error')}")
                    continue
                
                pages_crawled += 1
                
                # Extract images
                html = scrape_result.get("html", "")
                content = scrape_result.get("content", "")
                images = await extract_images_from_content(content, html, url)
                
                if images:
                    total_images_found += len(images)
                    
                    # Process images (detect tigers, identify, create evidence)
                    processing_result = await process_crawled_images(
                        images,
                        facility_id,
                        url,
                        session,
                        is_reference_facility=is_reference
                    )
                    
                    total_tigers_detected += processing_result["tigers_detected"]
                    total_tigers_identified += processing_result["tigers_identified"]
                    total_evidence_created += processing_result["evidence_created"]
            
            except Exception as e:
                error_msg = f"Error crawling {platform} ({url}): {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        # Update facility last_crawled_at
        facility.last_crawled_at = datetime.utcnow()
        session.commit()
        
        # Calculate duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log crawl history with enhanced statistics
        crawl_record = CrawlHistory(
            facility_id=facility_id,
            source_url="social_media",
            status="completed",
            images_found=total_images_found,
            tigers_identified=total_tigers_identified,
            pages_crawled=pages_crawled,
            crawl_duration_ms=duration_ms,
            error_log=errors if errors else [],
            crawl_statistics={
                "tigers_detected": total_tigers_detected,
                "evidence_created": total_evidence_created,
                "platforms_crawled": len(sources_to_crawl),
                "is_reference_facility": is_reference
            },
            completed_at=datetime.utcnow()
        )
        session.add(crawl_record)
        session.commit()
        
        return {
            "facility_id": facility_id,
            "images_found": total_images_found,
            "tigers_detected": total_tigers_detected,
            "tigers_identified": total_tigers_identified,
            "evidence_created": total_evidence_created,
            "pages_crawled": pages_crawled,
            "duration_ms": duration_ms,
            "status": "completed",
            "errors": errors if errors else None
        }

