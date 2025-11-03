"""API routes for analytics and dashboards"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.analytics_service import get_analytics_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/investigations")
async def get_investigation_analytics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get investigation analytics"""
    try:
        service = get_analytics_service(db)
        
        # Parse date strings to datetime if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid end_date format: {end_date}")
        
        analytics = service.get_investigation_analytics(
            start_date=start_dt,
            end_date=end_dt,
            user_id=current_user.user_id
        )
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Error getting investigation analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting investigation analytics: {str(e)}")


@router.get("/evidence")
async def get_evidence_analytics(
    investigation_id: Optional[UUID] = Query(None, description="Investigation ID filter"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get evidence analytics"""
    try:
        service = get_analytics_service(db)
        
        # Parse date strings to datetime if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid end_date format: {end_date}")
        
        analytics = service.get_evidence_analytics(
            investigation_id=investigation_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Error getting evidence analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting evidence analytics: {str(e)}")


@router.get("/verification")
async def get_verification_analytics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get verification analytics"""
    try:
        service = get_analytics_service(db)
        
        # Parse date strings to datetime if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid end_date format: {end_date}")
        
        analytics = service.get_verification_analytics(
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Error getting verification analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting verification analytics: {str(e)}")


@router.get("/geographic")
async def get_geographic_analytics(
    investigation_id: Optional[UUID] = Query(None, description="Investigation ID filter"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get geographic analytics"""
    try:
        service = get_analytics_service(db)
        analytics = service.get_geographic_analytics(
            investigation_id=investigation_id
        )
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Error getting geographic analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting geographic analytics: {str(e)}")


@router.get("/facilities")
async def get_facility_analytics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get facility analytics"""
    try:
        service = get_analytics_service(db)
        
        # Parse date strings to datetime if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid end_date format: {end_date}")
        
        analytics = service.get_facility_analytics(
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Error getting facility analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting facility analytics: {str(e)}")


@router.get("/tigers")
async def get_tiger_analytics(
    investigation_id: Optional[UUID] = Query(None, description="Investigation ID filter"),
    facility_id: Optional[UUID] = Query(None, description="Facility ID filter"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get tiger analytics"""
    try:
        service = get_analytics_service(db)
        analytics = service.get_tiger_analytics(
            investigation_id=investigation_id,
            facility_id=facility_id
        )
        
        # Add missing fields that frontend expects
        if "identification_rate" not in analytics:
            analytics["identification_rate"] = 0
        if "trends" not in analytics:
            analytics["trends"] = []
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Error getting tiger analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting tiger analytics: {str(e)}")


@router.get("/agents")
async def get_agent_performance_analytics(
    investigation_id: Optional[UUID] = Query(None, description="Investigation ID filter"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get agent performance analytics"""
    try:
        service = get_analytics_service(db)
        
        # Parse date strings to datetime if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid end_date format: {end_date}")
        
        analytics = service.get_agent_performance_analytics(
            investigation_id=investigation_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Error getting agent analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting agent analytics: {str(e)}")

