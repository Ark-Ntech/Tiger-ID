"""Optimized dashboard routes with batched queries"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.simple_cache import cached

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@cached(ttl_minutes=5)
def get_dashboard_stats_cached(db):
    """Get all dashboard stats in a single optimized query"""
    # Use a single query to get all counts at once
    result = db.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM investigations) as investigation_count,
            (SELECT COUNT(*) FROM tigers) as tiger_count,
            (SELECT COUNT(*) FROM facilities) as facility_count,
            (SELECT COUNT(*) FROM evidence) as evidence_count,
            (SELECT COUNT(*) FROM users) as user_count,
            (SELECT COUNT(*) FROM verification_queue) as verification_count
    """)).fetchone()
    
    return {
        "investigations": {
            "total": result[0],
            "active": 0,
            "completed": 0,
            "pending": 0
        },
        "tigers": {
            "total": result[1],
            "identified": 0,
            "unidentified": 0
        },
        "facilities": {
            "total": result[2],
            "monitored": result[2],
            "flagged": 0
        },
        "evidence": {
            "total": result[3],
            "verified": 0,
            "pending": result[3]
        },
        "users": {
            "total": result[4],
            "active": result[4]
        },
        "verification": {
            "pending": result[5],
            "total": result[5]
        }
    }

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get all dashboard statistics in a single optimized request"""
    try:
        stats = get_dashboard_stats_cached(db)
        return {"success": True, "data": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}
