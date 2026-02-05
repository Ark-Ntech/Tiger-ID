"""
Discovery Scheduler

Orchestrates continuous tiger discovery across all TPC facilities using FREE tools only.

Integrates with existing systems:
- FacilityCrawlerService: Website crawling + DuckDuckGo search
- ImagePipelineService: Image processing and identification
- DeepResearchServer: DuckDuckGo-powered facility research
- ImageSearchService: Reverse image search capabilities
- AutoDiscoveryService: Record creation and management
- TigerService: Tiger identification pipeline

No additional API keys required - uses only existing infrastructure.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.config.settings import get_settings
from backend.database import get_db_session
from backend.database.models import Facility, Tiger, TigerImage, CrawlHistory
from backend.services.facility_crawler_service import FacilityCrawlerService, DiscoveredImage
from backend.services.image_pipeline_service import ImagePipelineService
from backend.mcp_servers.deep_research_server import get_deep_research_server
from backend.utils.logging import get_logger

# Try to import APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False

logger = get_logger(__name__)


class DiscoveryScheduler:
    """
    Orchestrates continuous tiger discovery using FREE tools only.

    Integrates:
    - DuckDuckGo search (Deep Research Server)
    - Playwright website crawling
    - OpenCV image quality assessment
    - Modal GPU for ReID models
    - Database vector search

    No Meta, YouTube, Firecrawl, or other paid APIs required.
    """

    def __init__(self):
        """Initialize the discovery scheduler."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False

        # Configuration from settings (properly loads from .env)
        settings = get_settings()
        self.enabled = settings.discovery.enabled
        self.batch_size = settings.discovery.batch_size
        self.interval_hours = settings.discovery.interval_hours
        self.max_facilities_per_run = settings.discovery.max_facilities

        # Statistics
        self._stats = {
            "total_crawls": 0,
            "total_images_found": 0,
            "total_tigers_discovered": 0,
            "last_crawl_time": None,
            "started_at": None,
            "errors": 0
        }

        logger.info(f"DiscoveryScheduler initialized (enabled: {self.enabled}, interval: {self.interval_hours}h)")

    def start(self) -> bool:
        """
        Start the continuous discovery scheduler.

        Returns:
            True if started successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Discovery scheduler is disabled (DISCOVERY_ENABLED=false)")
            return False

        if not HAS_APSCHEDULER:
            logger.error("APScheduler not installed. Install with: pip install apscheduler")
            return False

        if self._running:
            logger.warning("Discovery scheduler is already running")
            return True

        self.scheduler = AsyncIOScheduler()

        # Schedule priority facility crawl (every N hours)
        self.scheduler.add_job(
            self._crawl_priority_facilities,
            IntervalTrigger(hours=self.interval_hours),
            id='crawl_priority',
            name='Crawl high-priority facilities',
            replace_existing=True
        )

        # Schedule full crawl (weekly, Sunday 2 AM)
        self.scheduler.add_job(
            self._crawl_all_facilities,
            CronTrigger(day_of_week='sun', hour=2),
            id='crawl_all',
            name='Weekly full facility crawl',
            replace_existing=True
        )

        # Schedule pending image processing (every hour)
        self.scheduler.add_job(
            self._process_pending_images,
            IntervalTrigger(hours=1),
            id='process_images',
            name='Process pending images',
            replace_existing=True
        )

        # Schedule deep research update (daily at 4 AM)
        self.scheduler.add_job(
            self._run_deep_research,
            CronTrigger(hour=4),
            id='deep_research',
            name='Deep research facility updates',
            replace_existing=True
        )

        self.scheduler.start()
        self._running = True
        self._stats["started_at"] = datetime.utcnow().isoformat()

        logger.info("Discovery scheduler started (FREE tools only)")
        logger.info(f"  - Priority crawl: every {self.interval_hours} hours")
        logger.info(f"  - Full crawl: weekly (Sundays 2 AM)")
        logger.info(f"  - Image processing: every hour")
        logger.info(f"  - Deep research: daily at 4 AM")

        return True

    def stop(self):
        """Stop the discovery scheduler."""
        if self.scheduler and self._running:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Discovery scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            **self._stats,
            "is_running": self._running,
            "enabled": self.enabled,
            "interval_hours": self.interval_hours,
            "batch_size": self.batch_size,
            "tools_used": [
                "duckduckgo_search",
                "playwright_crawling",
                "opencv_quality",
                "megadetector_detection",
                "modal_gpu_reid"
            ]
        }

    async def _crawl_priority_facilities(self):
        """
        Crawl high-priority facilities.

        Prioritizes:
        1. Reference facilities with high tiger counts
        2. Facilities not crawled recently
        3. Facilities with social media links
        """
        logger.info("Starting priority facility crawl...")

        try:
            with get_db_session() as db:
                crawler = FacilityCrawlerService(db)
                pipeline = ImagePipelineService(db)

                # Get priority facilities
                cutoff = datetime.utcnow() - timedelta(days=7)
                facilities = db.query(Facility).filter(
                    Facility.is_reference_facility == True,
                    Facility.tiger_count >= 3,
                    or_(
                        Facility.last_crawled_at.is_(None),
                        Facility.last_crawled_at < cutoff
                    )
                ).order_by(
                    Facility.tiger_count.desc(),
                    Facility.last_crawled_at.asc().nulls_first()
                ).limit(self.max_facilities_per_run).all()

                logger.info(f"Found {len(facilities)} priority facilities to crawl")

                total_images = 0
                total_tigers = 0

                for facility in facilities:
                    try:
                        # Crawl facility
                        images = await crawler.crawl_facility(facility)
                        total_images += len(images)

                        # Process discovered images
                        if images:
                            processed = await pipeline.process_discovered_images(images, facility)
                            total_tigers += sum(1 for p in processed if p.is_new)

                    except Exception as e:
                        logger.error(f"Error processing {facility.exhibitor_name}: {e}")
                        self._stats["errors"] += 1

                # Cleanup
                await crawler.close()
                await pipeline.close()

            # Update stats
            self._stats["total_crawls"] += 1
            self._stats["total_images_found"] += total_images
            self._stats["total_tigers_discovered"] += total_tigers
            self._stats["last_crawl_time"] = datetime.utcnow().isoformat()

            logger.info(f"Priority crawl complete: {total_images} images, {total_tigers} new tigers")

        except Exception as e:
            logger.error(f"Priority crawl failed: {e}")
            self._stats["errors"] += 1

    async def _crawl_all_facilities(self):
        """Full crawl of all TPC facilities (weekly)."""
        logger.info("Starting full facility crawl...")

        try:
            with get_db_session() as db:
                crawler = FacilityCrawlerService(db)

                stats = await crawler.crawl_all_facilities(
                    batch_size=self.batch_size
                )

                await crawler.close()

            self._stats["total_crawls"] += 1
            self._stats["total_images_found"] += stats.get("images_found", 0)

            logger.info(f"Full crawl complete: {stats}")

        except Exception as e:
            logger.error(f"Full crawl failed: {e}")
            self._stats["errors"] += 1

    async def _process_pending_images(self):
        """
        Process any pending discovered images.

        This handles images that were crawled but not yet processed.
        """
        logger.info("Processing pending images...")

        try:
            with get_db_session() as db:
                # Find unprocessed crawl records
                pending_crawls = db.query(CrawlHistory).filter(
                    CrawlHistory.status == "completed",
                    CrawlHistory.tigers_identified == 0,
                    CrawlHistory.images_found > 0
                ).limit(20).all()

                if not pending_crawls:
                    logger.debug("No pending images to process")
                    return

                logger.info(f"Found {len(pending_crawls)} crawls with unprocessed images")

                # This is a placeholder - in production, you'd re-process
                # the images from these crawls through the pipeline

        except Exception as e:
            logger.error(f"Pending image processing failed: {e}")

    async def _run_deep_research(self):
        """
        Run deep research on facilities using DuckDuckGo.

        Gathers updated intelligence about facilities and their tigers.
        """
        logger.info("Starting deep research update...")

        try:
            deep_research = get_deep_research_server()

            with get_db_session() as db:
                # Get facilities needing research
                facilities = db.query(Facility).filter(
                    Facility.is_reference_facility == True,
                    Facility.tiger_count >= 5
                ).limit(20).all()

                for facility in facilities:
                    try:
                        # Start research session
                        result = await deep_research._handle_start_research(
                            topic=facility.exhibitor_name,
                            mode="facility_investigation",
                            depth="standard"
                        )

                        if result.get("success"):
                            session_id = result.get("session_id")

                            # Expand research
                            await deep_research._handle_expand_research(
                                session_id=session_id,
                                direction="tiger news violations"
                            )

                            # Synthesize findings
                            synthesis = await deep_research._handle_synthesize(
                                session_id=session_id
                            )

                            if synthesis.get("success"):
                                logger.info(f"Research complete for {facility.exhibitor_name}")

                    except Exception as e:
                        logger.warning(f"Research failed for {facility.exhibitor_name}: {e}")

            logger.info("Deep research update complete")

        except Exception as e:
            logger.error(f"Deep research failed: {e}")

    # Manual trigger methods for API endpoints

    async def trigger_facility_crawl(self, facility_id: UUID) -> Dict[str, Any]:
        """
        Manually trigger crawl for a specific facility.

        Args:
            facility_id: UUID of facility to crawl

        Returns:
            Crawl results
        """
        with get_db_session() as db:
            facility = db.query(Facility).filter(
                Facility.facility_id == facility_id
            ).first()

            if not facility:
                return {"error": f"Facility {facility_id} not found"}

            crawler = FacilityCrawlerService(db)
            pipeline = ImagePipelineService(db)

            try:
                images = await crawler.crawl_facility(facility)
                processed = await pipeline.process_discovered_images(images, facility)

                return {
                    "facility_id": str(facility_id),
                    "facility_name": facility.exhibitor_name,
                    "images_found": len(images),
                    "tigers_processed": len(processed),
                    "new_tigers": sum(1 for p in processed if p.is_new),
                    "tools_used": ["duckduckgo", "playwright", "opencv", "modal_gpu"]
                }

            finally:
                await crawler.close()
                await pipeline.close()

    async def trigger_full_crawl(self) -> Dict[str, Any]:
        """
        Manually trigger full crawl of all facilities.

        Returns:
            Job status
        """
        if self._running and self.scheduler:
            # Run immediately using scheduler
            self.scheduler.add_job(
                self._crawl_all_facilities,
                trigger='date',
                id='manual_crawl',
                replace_existing=True
            )
            return {"status": "crawl_queued", "method": "free_tools_only"}
        else:
            # Run directly
            await self._crawl_all_facilities()
            return {"status": "crawl_complete", "method": "free_tools_only"}


# Singleton instance
_scheduler_instance: Optional[DiscoveryScheduler] = None


def get_discovery_scheduler() -> DiscoveryScheduler:
    """Get or create the singleton scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DiscoveryScheduler()
    return _scheduler_instance


def start_discovery_scheduler() -> bool:
    """Start the discovery scheduler."""
    scheduler = get_discovery_scheduler()
    return scheduler.start()


def stop_discovery_scheduler():
    """Stop the discovery scheduler."""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
