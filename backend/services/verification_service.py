"""Service layer for Verification operations"""

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.database.models import VerificationQueue


class VerificationService:
    """Service for verification queue operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_verification_request(
        self,
        entity_type: str,
        entity_id: UUID,
        priority: str = "medium",
        assigned_to: Optional[UUID] = None
    ) -> VerificationQueue:
        """Create a new verification request"""
        queue_item = VerificationQueue(
            entity_type=entity_type,
            entity_id=entity_id,
            priority=priority,
            requires_human_review=True,
            assigned_to=assigned_to,
            status="pending"
        )
        self.session.add(queue_item)
        self.session.commit()
        self.session.refresh(queue_item)
        return queue_item
    
    def get_verification_queue(
        self,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[VerificationQueue]:
        """Get verification queue items with filters"""
        query = self.session.query(VerificationQueue)
        
        if status:
            query = query.filter(VerificationQueue.status == status)
        else:
            # Default to pending items
            query = query.filter(VerificationQueue.status == "pending")
        
        if assigned_to:
            query = query.filter(VerificationQueue.assigned_to == assigned_to)
        
        if priority:
            query = query.filter(VerificationQueue.priority == priority)
        
        # Order by priority and creation date
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(
            query.limit(limit).offset(offset).all(),
            key=lambda x: (priority_order.get(x.priority, 3), x.created_at)
        )
    
    def approve_verification(
        self,
        queue_id: UUID,
        reviewed_by: UUID,
        review_notes: Optional[str] = None
    ) -> Optional[VerificationQueue]:
        """Approve a verification request"""
        queue_item = self.session.query(VerificationQueue).filter(
            VerificationQueue.queue_id == queue_id
        ).first()
        
        if not queue_item:
            return None
        
        queue_item.status = "approved"
        queue_item.reviewed_by = reviewed_by
        queue_item.reviewed_at = datetime.utcnow()
        if review_notes:
            queue_item.review_notes = review_notes
        
        self.session.commit()
        self.session.refresh(queue_item)
        return queue_item
    
    def reject_verification(
        self,
        queue_id: UUID,
        reviewed_by: UUID,
        review_notes: Optional[str] = None
    ) -> Optional[VerificationQueue]:
        """Reject a verification request"""
        queue_item = self.session.query(VerificationQueue).filter(
            VerificationQueue.queue_id == queue_id
        ).first()
        
        if not queue_item:
            return None
        
        queue_item.status = "rejected"
        queue_item.reviewed_by = reviewed_by
        queue_item.reviewed_at = datetime.utcnow()
        if review_notes:
            queue_item.review_notes = review_notes
        
        self.session.commit()
        self.session.refresh(queue_item)
        return queue_item
    
    def assign_verification(
        self,
        queue_id: UUID,
        assigned_to: UUID
    ) -> Optional[VerificationQueue]:
        """Assign a verification request to a user"""
        queue_item = self.session.query(VerificationQueue).filter(
            VerificationQueue.queue_id == queue_id
        ).first()
        
        if not queue_item:
            return None
        
        queue_item.assigned_to = assigned_to
        queue_item.status = "in_review"
        self.session.commit()
        self.session.refresh(queue_item)
        return queue_item

