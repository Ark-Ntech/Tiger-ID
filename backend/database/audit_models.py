"""Audit logging models (SQLite-compatible)"""

from sqlalchemy import Column, String, Text, DateTime, Index, ForeignKey, text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.database.models import Base, generate_uuid


class AuditLog(Base):
    """Audit log for tracking system actions"""
    __tablename__ = "audit_logs"

    audit_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    action_type = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(36), nullable=True)
    action_details = Column(Text, nullable=True)  # JSON as Text for SQLite
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action_type"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_status", "status"),
    )
