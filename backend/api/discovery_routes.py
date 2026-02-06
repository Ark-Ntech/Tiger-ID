"""
Discovery API Routes

Endpoints for controlling the continuous tiger discovery pipeline.

All operations use FREE tools only:
- DuckDuckGo search (no API key)
- Playwright browser automation (local)
- OpenCV image processing (local)
- Modal GPU for ReID models (existing infrastructure)
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.database import get_db
from backend.database.models import Facility, Tiger, TigerImage, CrawlHistory
from backend.services.discovery_scheduler import (
    get_discovery_scheduler,
    start_discovery_scheduler,
    stop_discovery_scheduler
)
from backend.services.facility_crawler_service import FacilityCrawlerService
from backend.services.image_pipeline_service import ImagePipelineService
from backend.mcp_servers.deep_research_server import get_deep_research_server
from backend.utils.logging import get_logger
from pydantic import BaseModel
from enum import Enum

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


# ============================================================================
# Pydantic models for response schemas
# ============================================================================

class TimeRange(str, Enum):
    """Time range filter options."""
    last_24h = "24h"
    last_7d = "7d"
    last_30d = "30d"


class AutoInvestigationStatus(str, Enum):
    """Status filter options for auto-investigations."""
    all = "all"
    completed = "completed"
    failed = "failed"
    pending = "pending"
    active = "active"


@router.get("/status")
async def get_discovery_status():
    """
    Get the current status of the discovery scheduler.

    Returns scheduler state, statistics, and tools being used.
    """
    scheduler = get_discovery_scheduler()
    stats = scheduler.get_stats()

    return {
        "status": "running" if scheduler.is_running() else "stopped",
        "enabled": stats["enabled"],
        **stats
    }


@router.post("/start")
async def start_scheduler():
    """
    Start the continuous discovery scheduler.

    The scheduler will:
    - Crawl priority facilities every N hours (default: 6)
    - Run full crawl weekly (Sundays at 2 AM)
    - Process pending images hourly
    - Run deep research daily

    Requires DISCOVERY_ENABLED=true in environment.
    """
    scheduler = get_discovery_scheduler()

    if scheduler.is_running():
        return {"status": "already_running", "message": "Scheduler is already running"}

    success = scheduler.start()

    if success:
        return {
            "status": "started",
            "message": "Discovery scheduler started (FREE tools only)",
            "tools_used": [
                "duckduckgo_search",
                "playwright_crawling",
                "opencv_quality",
                "modal_gpu_reid"
            ]
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to start scheduler. Check DISCOVERY_ENABLED setting."
        )


@router.post("/stop")
async def stop_scheduler():
    """Stop the continuous discovery scheduler."""
    scheduler = get_discovery_scheduler()

    if not scheduler.is_running():
        return {"status": "not_running", "message": "Scheduler is not running"}

    scheduler.stop()
    return {"status": "stopped", "message": "Discovery scheduler stopped"}


@router.post("/crawl/facility/{facility_id}")
async def crawl_single_facility(
    facility_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Manually trigger crawl for a specific facility.

    This will:
    1. Search DuckDuckGo for facility information
    2. Crawl the facility website with Playwright
    3. Search DuckDuckGo Images for tiger photos
    4. Process any discovered images through the ID pipeline

    All using FREE tools only (no paid APIs).
    """
    facility = db.query(Facility).filter(
        Facility.facility_id == facility_id
    ).first()

    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility {facility_id} not found")

    scheduler = get_discovery_scheduler()

    try:
        result = await scheduler.trigger_facility_crawl(facility_id)
        return result
    except Exception as e:
        logger.error(f"Crawl failed for facility {facility_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl/all")
async def trigger_full_crawl(background_tasks: BackgroundTasks):
    """
    Trigger a full crawl of all TPC facilities.

    This runs in the background and may take several hours.
    Uses FREE tools only (DuckDuckGo, Playwright, OpenCV).
    """
    scheduler = get_discovery_scheduler()

    async def run_crawl():
        try:
            await scheduler._crawl_all_facilities()
        except Exception as e:
            logger.error(f"Full crawl failed: {e}")

    background_tasks.add_task(run_crawl)

    return {
        "status": "crawl_started",
        "message": "Full crawl started in background",
        "method": "free_tools_only",
        "tools_used": ["duckduckgo", "playwright", "opencv", "modal_gpu"]
    }


@router.get("/stats")
async def get_discovery_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive discovery statistics.

    Returns counts of facilities, tigers, images, and crawl history.
    Optimized to use fewer database queries (4 queries instead of 12+).
    """
    from sqlalchemy import case

    # Facility stats - single query with case expressions
    facility_stats = db.query(
        func.count(Facility.facility_id).label('total'),
        func.count(case((Facility.is_reference_facility == True, 1))).label('reference'),
        func.count(case((Facility.last_crawled_at.isnot(None), 1))).label('crawled'),
        func.count(case((Facility.website.isnot(None), 1))).label('with_website'),
        func.count(case((Facility.social_media_links != {}, 1))).label('with_social')
    ).first()

    total_facilities = facility_stats.total or 0
    ref_facilities = facility_stats.reference or 0
    facilities_crawled = facility_stats.crawled or 0
    facilities_with_website = facility_stats.with_website or 0
    facilities_with_social = facility_stats.with_social or 0

    # Tiger stats - single query with case expressions
    tiger_stats = db.query(
        func.count(Tiger.tiger_id).label('total'),
        func.count(case((Tiger.discovered_at.isnot(None), 1))).label('discovered'),
        func.count(case((Tiger.is_reference == True, 1))).label('reference')
    ).first()

    total_tigers = tiger_stats.total or 0
    discovered_tigers = tiger_stats.discovered or 0
    reference_tigers = tiger_stats.reference or 0

    # Image stats - single query with case expressions
    image_stats = db.query(
        func.count(TigerImage.image_id).label('total'),
        func.count(case((TigerImage.is_reference == False, 1))).label('discovered'),
        func.count(case((TigerImage.verified == True, 1))).label('verified')
    ).first()

    total_images = image_stats.total or 0
    discovered_images = image_stats.discovered or 0
    verified_images = image_stats.verified or 0

    # Crawl history - single query with case expressions
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    crawl_stats = db.query(
        func.count(CrawlHistory.crawl_id).label('total'),
        func.count(case((CrawlHistory.status == "completed", 1))).label('successful'),
        func.count(case((CrawlHistory.crawled_at >= cutoff_date, 1))).label('recent')
    ).first()

    total_crawls = crawl_stats.total or 0
    successful_crawls = crawl_stats.successful or 0
    recent_crawls = crawl_stats.recent or 0

    # Scheduler stats
    scheduler = get_discovery_scheduler()
    scheduler_stats = scheduler.get_stats()

    return {
        "facilities": {
            "total": total_facilities,
            "reference": ref_facilities,
            "crawled": facilities_crawled,
            "with_website": facilities_with_website,
            "with_social_media": facilities_with_social,
            "pending_crawl": ref_facilities - facilities_crawled
        },
        "tigers": {
            "total": total_tigers,
            "discovered": discovered_tigers,
            "reference": reference_tigers,
            "real": total_tigers - reference_tigers
        },
        "images": {
            "total": total_images,
            "discovered": discovered_images,
            "verified": verified_images
        },
        "crawls": {
            "total": total_crawls,
            "successful": successful_crawls,
            "recent_7_days": recent_crawls
        },
        "scheduler": {
            "running": scheduler.is_running(),
            "enabled": scheduler_stats["enabled"],
            "total_crawls": scheduler_stats["total_crawls"],
            "last_crawl": scheduler_stats["last_crawl_time"]
        },
        "tools_used": [
            "duckduckgo (free)",
            "playwright (local)",
            "opencv (local)",
            "modal_gpu (existing)"
        ]
    }


@router.get("/queue")
async def get_crawl_queue(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    days_old: int = Query(7, ge=1, le=30)
):
    """
    Get facilities pending crawl.

    Returns facilities that:
    - Are reference facilities (from TPC data)
    - Have a website URL
    - Haven't been crawled in N days (default: 7)

    Sorted by tiger count (highest first).
    """
    cutoff = datetime.utcnow() - timedelta(days=days_old)

    facilities = db.query(Facility).filter(
        Facility.is_reference_facility == True,
        Facility.website.isnot(None),
        or_(
            Facility.last_crawled_at.is_(None),
            Facility.last_crawled_at < cutoff
        )
    ).order_by(
        Facility.tiger_count.desc()
    ).limit(limit).all()

    def _parse_coords(facility):
        """Extract lat/lng from facility coordinates JSON."""
        if facility.coordinates:
            try:
                import json
                coords = json.loads(facility.coordinates) if isinstance(facility.coordinates, str) else facility.coordinates
                if coords:
                    return coords.get("latitude"), coords.get("longitude")
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
        return None, None

    return {
        "count": len(facilities),
        "days_since_crawl": days_old,
        "facilities": [
            {
                "facility_id": str(f.facility_id),
                "exhibitor_name": f.exhibitor_name,
                "state": f.state,
                "city": f.city,
                "tiger_count": f.tiger_count,
                "website": f.website,
                "has_social_media": bool(f.social_media_links),
                "latitude": _parse_coords(f)[0],
                "longitude": _parse_coords(f)[1],
                "last_crawled_at": f.last_crawled_at.isoformat() if f.last_crawled_at else None
            }
            for f in facilities
        ]
    }


@router.get("/history")
async def get_crawl_history(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    facility_id: Optional[UUID] = None,
    status: Optional[str] = None
):
    """
    Get crawl history records.

    Optionally filter by facility_id or status.
    """
    query = db.query(CrawlHistory)

    if facility_id:
        query = query.filter(CrawlHistory.facility_id == facility_id)

    if status:
        query = query.filter(CrawlHistory.status == status)

    crawls = query.order_by(
        CrawlHistory.crawled_at.desc()
    ).limit(limit).all()

    return {
        "count": len(crawls),
        "crawls": [
            {
                "crawl_id": str(c.crawl_id),
                "facility_id": str(c.facility_id) if c.facility_id else None,
                "source_url": c.source_url,
                "status": c.status,
                "images_found": c.images_found,
                "tigers_identified": c.tigers_identified,
                "crawled_at": c.crawled_at.isoformat() if c.crawled_at else None,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                "duration_ms": c.crawl_duration_ms,
                "error": c.error_message
            }
            for c in crawls
        ]
    }


@router.post("/research/{facility_id}")
async def run_deep_research(
    facility_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Run deep research on a specific facility using DuckDuckGo.

    This uses the Deep Research Server to gather intelligence about
    the facility from web sources.
    """
    facility = db.query(Facility).filter(
        Facility.facility_id == facility_id
    ).first()

    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility {facility_id} not found")

    deep_research = get_deep_research_server()

    try:
        # Start research session
        result = await deep_research._handle_start_research(
            topic=facility.exhibitor_name,
            mode="facility_investigation",
            depth="deep"
        )

        if not result.get("success"):
            return {"error": result.get("error", "Research failed")}

        session_id = result.get("session_id")

        # Expand research with tiger-specific queries
        await deep_research._handle_expand_research(
            session_id=session_id,
            direction="tiger violations news"
        )

        # Synthesize findings
        synthesis = await deep_research._handle_synthesize(
            session_id=session_id
        )

        return {
            "facility_id": str(facility_id),
            "facility_name": facility.exhibitor_name,
            "research_session_id": session_id,
            "queries_executed": result.get("queries_executed", 0),
            "results_found": result.get("results_found", 0),
            "synthesis": synthesis.get("synthesis") if synthesis.get("success") else None,
            "tool_used": "duckduckgo (free)"
        }

    except Exception as e:
        logger.error(f"Deep research failed for {facility.exhibitor_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Auto-Investigation Statistics Endpoints
# ============================================================================

@router.get("/auto-investigation/stats")
async def get_auto_investigation_stats(
    db: Session = Depends(get_db),
    time_range: TimeRange = Query(TimeRange.last_24h, description="Time range filter")
):
    """
    Get statistics for auto-triggered investigations.

    Returns aggregate statistics including:
    - Total investigations triggered
    - Completed, failed, and pending counts
    - Average duration in milliseconds

    Filterable by time range (24h, 7d, 30d).
    """
    from backend.database.models import Investigation, InvestigationStatus, InvestigationStep

    # Calculate cutoff time based on time range
    if time_range == TimeRange.last_24h:
        cutoff = datetime.utcnow() - timedelta(hours=24)
    elif time_range == TimeRange.last_7d:
        cutoff = datetime.utcnow() - timedelta(days=7)
    else:  # last_30d
        cutoff = datetime.utcnow() - timedelta(days=30)

    # Query auto-discovery investigations within time range
    base_query = db.query(Investigation).filter(
        Investigation.source == "auto_discovery",
        Investigation.created_at >= cutoff
    )

    total_triggered = base_query.count()

    # Count by status
    completed = base_query.filter(
        Investigation.status == InvestigationStatus.completed.value
    ).count()

    failed = base_query.filter(
        Investigation.status == InvestigationStatus.cancelled.value
    ).count()

    # Pending includes draft and active
    pending = base_query.filter(
        Investigation.status.in_([
            InvestigationStatus.draft.value,
            InvestigationStatus.active.value,
            InvestigationStatus.pending_verification.value
        ])
    ).count()

    # Calculate average duration for completed investigations
    completed_investigations = base_query.filter(
        Investigation.status == InvestigationStatus.completed.value,
        Investigation.completed_at.isnot(None),
        Investigation.started_at.isnot(None)
    ).all()

    avg_duration_ms = 0
    if completed_investigations:
        total_duration = sum(
            (inv.completed_at - inv.started_at).total_seconds() * 1000
            for inv in completed_investigations
            if inv.completed_at and inv.started_at
        )
        avg_duration_ms = int(total_duration / len(completed_investigations))

    return {
        "time_range": time_range.value,
        "total_triggered": total_triggered,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "avg_duration_ms": avg_duration_ms,
        "cutoff_time": cutoff.isoformat()
    }


@router.get("/auto-investigation/recent")
async def get_recent_auto_investigations(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    status: Optional[AutoInvestigationStatus] = Query(
        None,
        description="Filter by investigation status"
    )
):
    """
    Get recent auto-triggered investigations.

    Returns a list of recent auto-investigations with details including:
    - Investigation ID and status
    - Facility name and tiger name (if available)
    - Created and completed timestamps

    Optionally filterable by status.
    """
    from backend.database.models import Investigation, InvestigationStatus

    query = db.query(Investigation).filter(
        Investigation.source == "auto_discovery"
    )

    # Apply status filter
    if status and status != AutoInvestigationStatus.all:
        if status == AutoInvestigationStatus.completed:
            query = query.filter(Investigation.status == InvestigationStatus.completed.value)
        elif status == AutoInvestigationStatus.failed:
            query = query.filter(Investigation.status == InvestigationStatus.cancelled.value)
        elif status == AutoInvestigationStatus.pending:
            query = query.filter(Investigation.status.in_([
                InvestigationStatus.draft.value,
                InvestigationStatus.pending_verification.value
            ]))
        elif status == AutoInvestigationStatus.active:
            query = query.filter(Investigation.status == InvestigationStatus.active.value)

    # Order by most recent first
    investigations = query.order_by(
        Investigation.created_at.desc()
    ).limit(limit).all()

    results = []
    for inv in investigations:
        # Extract facility name from related_facilities if available
        facility_name = None
        if inv.related_facilities:
            # related_facilities is a list of facility IDs
            facilities = inv.related_facilities if isinstance(inv.related_facilities, list) else []
            if facilities:
                facility = db.query(Facility).filter(
                    Facility.facility_id == facilities[0]
                ).first()
                if facility:
                    facility_name = facility.exhibitor_name

        # Extract tiger name from source_tiger_id if available
        tiger_name = None
        if inv.source_tiger_id:
            tiger = db.query(Tiger).filter(
                Tiger.tiger_id == inv.source_tiger_id
            ).first()
            if tiger:
                tiger_name = tiger.name

        results.append({
            "investigation_id": str(inv.investigation_id),
            "title": inv.title,
            "status": inv.status,
            "priority": inv.priority,
            "facility_name": facility_name,
            "tiger_name": tiger_name,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "started_at": inv.started_at.isoformat() if inv.started_at else None,
            "completed_at": inv.completed_at.isoformat() if inv.completed_at else None
        })

    return {
        "count": len(results),
        "limit": limit,
        "status_filter": status.value if status else "all",
        "investigations": results
    }


@router.get("/pipeline/stats")
async def get_pipeline_stats(db: Session = Depends(get_db)):
    """
    Get image pipeline processing statistics.

    Returns cumulative statistics from the ImagePipelineService:
    - Images processed
    - Duplicates skipped (via SHA256 deduplication)
    - Quality rejected (below threshold)
    - No tigers detected
    - Embedding failures
    - New vs existing tigers
    - Auto-investigations triggered

    Note: Statistics are from the current running service instance.
    For historical data, use the discovery stats endpoint.
    """
    from backend.database.models import TigerImage, Investigation

    # Get stats from a fresh pipeline service instance
    # (Note: In production, you might want to persist these stats)
    pipeline_service = ImagePipelineService(db)
    runtime_stats = pipeline_service.get_stats()

    # Also compute database-based historical stats
    total_discovered_images = db.query(TigerImage).filter(
        TigerImage.is_reference == False
    ).count()

    # Count images with content_hash (deduplication enabled)
    images_with_hash = db.query(TigerImage).filter(
        TigerImage.content_hash.isnot(None)
    ).count()

    # Count duplicate images (those marked as duplicate_of another)
    duplicates_in_db = db.query(TigerImage).filter(
        TigerImage.is_duplicate_of.isnot(None)
    ).count()

    # Count auto-discovery investigations
    auto_investigations_total = db.query(Investigation).filter(
        Investigation.source == "auto_discovery"
    ).count()

    # Count verified discovered images
    verified_discovered = db.query(TigerImage).filter(
        TigerImage.is_reference == False,
        TigerImage.verified == True
    ).count()

    return {
        "runtime_stats": runtime_stats,
        "database_stats": {
            "total_discovered_images": total_discovered_images,
            "images_with_content_hash": images_with_hash,
            "duplicates_detected": duplicates_in_db,
            "auto_investigations_triggered": auto_investigations_total,
            "verified_discovered_images": verified_discovered
        },
        "tools_used": [
            "opencv (local quality assessment)",
            "sha256 (deduplication)",
            "megadetector (tiger detection)",
            "modal_gpu (6-model ensemble)"
        ]
    }
