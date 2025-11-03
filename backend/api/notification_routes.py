"""API routes for notifications"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.notification_service import get_notification_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of notifications"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for current user"""
    service = get_notification_service(db)
    notifications = service.get_notifications(
        user_id=current_user.user_id,
        read=read,
        notification_type=notification_type,
        priority=priority,
        limit=limit,
        offset=offset
    )
    
    return {
        "notifications": [
            {
                "notification_id": str(n.notification_id),
                "notification_type": n.type,
                "title": n.title,
                "message": n.message,
                "priority": "normal",  # Extract from message prefix if present
                "read": n.read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "read_at": None,  # Model doesn't have read_at
                "investigation_id": str(n.related_entity_id) if n.related_entity_type == "investigation" else None,
                "evidence_id": str(n.related_entity_id) if n.related_entity_type == "evidence" else None,
                "metadata": {}  # Model doesn't have metadata
            }
            for n in notifications
        ],
        "count": len(notifications)
    }


@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications"""
    service = get_notification_service(db)
    count = service.get_unread_count(current_user.user_id)
    
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    service = get_notification_service(db)
    notification = service.mark_as_read(notification_id, current_user.user_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {
        "notification_id": str(notification_id),
        "read": True,
        "message": "Notification marked as read"
    }


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    service = get_notification_service(db)
    count = service.mark_all_as_read(current_user.user_id)
    
    return {
        "count": count,
        "message": f"{count} notifications marked as read"
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    service = get_notification_service(db)
    deleted = service.delete_notification(notification_id, current_user.user_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {
        "notification_id": str(notification_id),
        "message": "Notification deleted"
    }

