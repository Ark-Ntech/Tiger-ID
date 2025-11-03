"""Audit logging service for comprehensive system tracking"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from backend.database.audit_models import AuditLog
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for audit logging"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def log_action(
        self,
        action_type: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        action_details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an action to the audit log
        
        Args:
            action_type: Type of action (e.g., 'investigation_created', 'evidence_added')
            user_id: User who performed the action
            resource_type: Type of resource affected (e.g., 'investigation', 'evidence')
            resource_id: ID of resource affected
            action_details: Additional action details as JSON
            ip_address: IP address of the user
            user_agent: User agent string
            status: Action status ('success', 'failed', 'error')
            error_message: Error message if status is not 'success'
        
        Returns:
            Created audit log entry
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action_details=action_details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
            created_at=datetime.utcnow()
        )
        
        self.session.add(audit_entry)
        self.session.commit()
        self.session.refresh(audit_entry)
        
        return audit_entry
    
    def get_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit logs with filters
        
        Args:
            user_id: Filter by user ID
            action_type: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of audit log entries
        """
        query = self.session.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if status:
            query = query.filter(AuditLog.status == status)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        query = query.order_by(desc(AuditLog.created_at))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_audit_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit log summary statistics
        
        Args:
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            Summary statistics
        """
        query = self.session.query(AuditLog)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        logs = query.all()
        
        # Action type distribution
        action_counts = {}
        for log in logs:
            action = log.action_type
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Status distribution
        status_counts = {}
        for log in logs:
            status = log.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # User activity
        user_counts = {}
        for log in logs:
            if log.user_id:
                user_id_str = str(log.user_id)
                user_counts[user_id_str] = user_counts.get(user_id_str, 0) + 1
        
        return {
            "total_actions": len(logs),
            "action_type_distribution": action_counts,
            "status_distribution": status_counts,
            "user_activity": user_counts,
            "success_rate": (status_counts.get("success", 0) / len(logs) * 100) if logs else 0
        }


def get_audit_service(session: Session) -> AuditService:
    """Get audit service instance"""
    return AuditService(session)

