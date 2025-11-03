"""Crawl scheduler service for managing facility crawl schedules"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database import get_db_session, Facility, CrawlHistory
from backend.services.reference_data_service import ReferenceDataService
from backend.jobs.crawl_job import crawl_facility_social_media
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class CrawlSchedulerService:
    """Service for scheduling and managing facility crawls"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize crawl scheduler service
        
        Args:
            session: Database session (optional)
        """
        self.session = session
        if session:
            self.ref_service = ReferenceDataService(session)
    
    def get_crawl_priority(self, facility: Facility) -> int:
        """
        Calculate crawl priority for a facility
        
        Args:
            facility: Facility object
            
        Returns:
            Priority score (higher = more priority)
        """
        priority = 0
        
        # Reference facilities get highest priority
        if facility.is_reference_facility:
            priority += 100
        
        # Facilities with recent tiger sightings
        if facility.tiger_count and facility.tiger_count > 0:
            priority += facility.tiger_count * 10
        
        # Facilities with violations
        if facility.violation_history:
            priority += len(facility.violation_history) * 15
        
        # Facilities with social media (more to monitor)
        if facility.social_media_links:
            priority += len(facility.social_media_links) * 5
        
        # Facilities not crawled recently get boost
        if facility.last_crawled_at:
            days_since_crawl = (datetime.utcnow() - facility.last_crawled_at).days
            if days_since_crawl > 30:
                priority += 20
        else:
            priority += 30  # Never crawled
        
        return priority
    
    def get_facilities_due_for_crawl(
        self,
        max_facilities: int = 50,
        reference_facilities_only: bool = False,
        hours_since_last_crawl: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get facilities that are due for crawling
        
        Args:
            max_facilities: Maximum number of facilities to return
            reference_facilities_only: Only return reference facilities
            hours_since_last_crawl: Minimum hours since last crawl
            
        Returns:
            List of facilities due for crawl
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.get_facilities_due_for_crawl(max_facilities, reference_facilities_only, hours_since_last_crawl)
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_since_last_crawl)
        
        query = self.session.query(Facility).filter(
            or_(
                Facility.last_crawled_at < cutoff_time,
                Facility.last_crawled_at.is_(None)
            )
        )
        
        if reference_facilities_only:
            query = query.filter(Facility.is_reference_facility == True)
        
        facilities = query.all()
        
        # Calculate priorities and sort
        facilities_with_priority = []
        for facility in facilities:
            priority = self.get_crawl_priority(facility)
            facilities_with_priority.append({
                "facility_id": str(facility.facility_id),
                "facility_name": facility.exhibitor_name,
                "priority": priority,
                "last_crawled_at": facility.last_crawled_at.isoformat() if facility.last_crawled_at else None,
                "is_reference": facility.is_reference_facility or False,
                "has_social_media": bool(facility.social_media_links),
                "tiger_count": facility.tiger_count
            })
        
        # Sort by priority (descending)
        facilities_with_priority.sort(key=lambda x: x["priority"], reverse=True)
        
        return facilities_with_priority[:max_facilities]
    
    def schedule_crawl(
        self,
        facility_id: UUID,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule a crawl for a facility
        
        Args:
            facility_id: Facility ID to crawl
            priority: Crawl priority (high, medium, low)
            
        Returns:
            Scheduling result
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.schedule_crawl(facility_id, priority)
        
        facility = self.session.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        
        if not facility:
            return {"error": "Facility not found"}
        
        # Check if facility has URLs to crawl
        has_urls = bool(facility.social_media_links or facility.website)
        if not has_urls:
            return {"error": "Facility has no social media links or website to crawl"}
        
        # Schedule crawl task
        try:
            # Use Celery to schedule async crawl
            result = crawl_facility_social_media.delay(str(facility_id))
            
            return {
                "facility_id": str(facility_id),
                "task_id": result.id,
                "status": "scheduled",
                "priority": priority or "medium"
            }
        
        except Exception as e:
            logger.error(f"Failed to schedule crawl: {e}", exc_info=True)
            return {"error": str(e), "facility_id": str(facility_id)}
    
    def schedule_batch_crawl(
        self,
        facility_ids: Optional[List[UUID]] = None,
        max_facilities: int = 20,
        reference_facilities_only: bool = True
    ) -> Dict[str, Any]:
        """
        Schedule batch crawls for multiple facilities
        
        Args:
            facility_ids: Specific facility IDs (None to auto-select)
            max_facilities: Maximum facilities to schedule
            reference_facilities_only: Only schedule reference facilities
            
        Returns:
            Batch scheduling results
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.schedule_batch_crawl(facility_ids, max_facilities, reference_facilities_only)
        
        if facility_ids:
            facilities_to_crawl = self.session.query(Facility).filter(
                Facility.facility_id.in_(facility_ids)
            ).all()
        else:
            # Get facilities due for crawl
            facilities_due = self.get_facilities_due_for_crawl(
                max_facilities=max_facilities,
                reference_facilities_only=reference_facilities_only
            )
            facility_ids = [UUID(f["facility_id"]) for f in facilities_due]
            facilities_to_crawl = self.session.query(Facility).filter(
                Facility.facility_id.in_(facility_ids)
            ).all()
        
        scheduled = []
        failed = []
        
        for facility in facilities_to_crawl:
            try:
                result = self.schedule_crawl(facility.facility_id)
                
                if "error" not in result:
                    scheduled.append({
                        "facility_id": str(facility.facility_id),
                        "facility_name": facility.exhibitor_name,
                        "task_id": result.get("task_id")
                    })
                else:
                    failed.append({
                        "facility_id": str(facility.facility_id),
                        "error": result.get("error")
                    })
            
            except Exception as e:
                logger.error(f"Failed to schedule crawl for {facility.facility_id}: {e}")
                failed.append({
                    "facility_id": str(facility.facility_id),
                    "error": str(e)
                })
        
        return {
            "scheduled_count": len(scheduled),
            "failed_count": len(failed),
            "scheduled": scheduled,
            "failed": failed
        }
    
    def get_crawl_statistics(
        self,
        facility_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get crawl statistics
        
        Args:
            facility_id: Optional facility ID (None for all facilities)
            days: Number of days to analyze
            
        Returns:
            Crawl statistics
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.get_crawl_statistics(facility_id, days)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.session.query(CrawlHistory).filter(
            CrawlHistory.crawled_at >= cutoff_date
        )
        
        if facility_id:
            query = query.filter(CrawlHistory.facility_id == facility_id)
        
        crawls = query.all()
        
        total_images = sum(c.images_found or 0 for c in crawls)
        total_tigers = sum(c.tigers_identified or 0 for c in crawls)
        successful_crawls = sum(1 for c in crawls if c.status == "completed")
        failed_crawls = sum(1 for c in crawls if c.status == "failed")
        
        avg_duration = sum(c.crawl_duration_ms or 0 for c in crawls) / len(crawls) if crawls else 0
        
        return {
            "total_crawls": len(crawls),
            "successful_crawls": successful_crawls,
            "failed_crawls": failed_crawls,
            "total_images_found": total_images,
            "total_tigers_identified": total_tigers,
            "average_duration_ms": int(avg_duration),
            "facility_id": str(facility_id) if facility_id else None,
            "days": days
        }


def get_crawl_scheduler_service(session: Optional[Session] = None) -> CrawlSchedulerService:
    """Get crawl scheduler service instance"""
    return CrawlSchedulerService(session)

