"""Notification service for user notifications"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database.models import Notification, User
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for managing user notifications"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        investigation_id: Optional[UUID] = None,
        evidence_id: Optional[UUID] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a notification
        
        Args:
            user_id: User ID to notify
            notification_type: Type of notification (evidence_found, phase_complete, error, etc.)
            title: Notification title
            message: Notification message
            investigation_id: Optional investigation ID
            evidence_id: Optional evidence ID
            priority: Priority level (low, normal, high, urgent)
            metadata: Optional metadata
        
        Returns:
            Created notification
        """
        # Map investigation_id/evidence_id to related_entity fields
        related_entity_type = None
        related_entity_id = None
        
        if investigation_id:
            related_entity_type = "investigation"
            related_entity_id = str(investigation_id)  # Convert UUID to string
        elif evidence_id:
            related_entity_type = "evidence"
            related_entity_id = str(evidence_id)  # Convert UUID to string
        
        notification = Notification(
            user_id=str(user_id),  # Convert UUID to string
            type=notification_type,  # Use 'type' not 'notification_type' to match model
            title=title,
            message=message,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            read=False
        )
        
        # Store priority and metadata in message or use summary field if available
        if priority != "normal":
            notification.message = f"[{priority.upper()}] {message}"
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        
        logger.info(
            f"Created notification",
            user_id=str(user_id),
            notification_type=notification_type,
            priority=priority
        )
        
        return notification
    
    def get_notifications(
        self,
        user_id: UUID,
        read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user
        
        Args:
            user_id: User ID
            read: Filter by read status (None = all)
            notification_type: Filter by notification type
            priority: Filter by priority
            limit: Maximum number of notifications
            offset: Offset for pagination
        
        Returns:
            List of notifications
        """
        # Convert UUID to string for SQLite comparison
        user_id_str = str(user_id)
        query = self.session.query(Notification).filter(
            Notification.user_id == user_id_str
        )
        
        if read is not None:
            query = query.filter(Notification.read == read)
        
        if notification_type:
            query = query.filter(Notification.type == notification_type)
        
        # Priority filtering - extract from message prefix [PRIORITY]
        if priority:
            # Filter by message prefix matching priority
            priority_prefix = f"[{priority.upper()}]"
            query = query.filter(Notification.message.like(f"%{priority_prefix}%"))
        
        return query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
    
    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        # Convert UUID to string for SQLite comparison
        user_id_str = str(user_id)
        return self.session.query(Notification).filter(
            and_(
                Notification.user_id == user_id_str,
                Notification.read == False
            )
        ).count()
    
    def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """Mark a notification as read"""
        # Convert UUIDs to strings for SQLite comparison
        notification_id_str = str(notification_id)
        user_id_str = str(user_id)
        notification = self.session.query(Notification).filter(
            and_(
                Notification.notification_id == notification_id_str,
                Notification.user_id == user_id_str
            )
        ).first()
        
        if notification:
            notification.read = True
            # Model doesn't have read_at field, skip it
            self.session.commit()
            self.session.refresh(notification)
        
        return notification
    
    def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user"""
        # Convert UUID to string for SQLite comparison
        user_id_str = str(user_id)
        count = self.session.query(Notification).filter(
            and_(
                Notification.user_id == user_id_str,
                Notification.read == False
            )
        ).update(
            {
                Notification.read: True
                # Model doesn't have read_at field
            },
            synchronize_session=False
        )
        self.session.commit()
        return count
    
    def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification"""
        notification = self.session.query(Notification).filter(
            and_(
                Notification.notification_id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if notification:
            self.session.delete(notification)
            self.session.commit()
            return True
        
        return False
    
    def create_investigation_notification(
        self,
        user_id: UUID,
        investigation_id: UUID,
        notification_type: str,
        message: str,
        priority: str = "normal"
    ) -> Notification:
        """Create an investigation-related notification"""
        from backend.services.investigation_service import InvestigationService
        
        investigation_service = InvestigationService(self.session)
        investigation = investigation_service.get_investigation(investigation_id)
        
        title = f"Investigation: {investigation.title if investigation else 'Unknown'}"
        
        # Add priority to message
        if priority != "normal":
            message = f"[{priority.upper()}] {message}"
        
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            related_entity_type="investigation",
            related_entity_id=investigation_id,
            read=False
        )
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        
        return notification
    
    def create_evidence_notification(
        self,
        user_id: UUID,
        evidence_id: UUID,
        investigation_id: Optional[UUID] = None,
        priority: str = "high"
    ) -> Notification:
        """Create an evidence-related notification"""
        # Use investigation_id for related_entity if provided
        related_entity_type = "investigation" if investigation_id else "evidence"
        related_entity_id = investigation_id if investigation_id else evidence_id
        
        notification = Notification(
            user_id=user_id,
            type="evidence_found",
            title="New Evidence Found",
            message=f"[{priority.upper()}] New evidence has been added to investigation",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            read=False
        )
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification
    
    def create_phase_complete_notification(
        self,
        user_id: UUID,
        investigation_id: UUID,
        phase: str,
        priority: str = "normal"
    ) -> Notification:
        """Create a phase completion notification"""
        return self.create_investigation_notification(
            user_id=user_id,
            investigation_id=investigation_id,
            notification_type="phase_complete",
            message=f"Phase '{phase}' completed",
            priority=priority
        )
    
    def create_error_notification(
        self,
        user_id: UUID,
        investigation_id: Optional[UUID],
        error_message: str,
        priority: str = "high"
    ) -> Notification:
        """Create an error notification"""
        return self.create_notification(
            user_id=user_id,
            notification_type="error",
            title="Investigation Error",
            message=error_message,
            investigation_id=investigation_id,
            priority=priority
        )


def get_notification_service(session: Session) -> NotificationService:
    """Get notification service instance"""
    return NotificationService(session)

