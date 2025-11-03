"""Tests for AuditService"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from backend.services.audit_service import AuditService
from backend.database.audit_models import AuditLog


class TestAuditService:
    """Tests for AuditService"""
    
    def test_log_action(self, db_session, sample_user_id):
        """Test logging an action"""
        service = AuditService(db_session)
        
        audit_entry = service.log_action(
            action_type="investigation_created",
            user_id=sample_user_id,
            resource_type="investigation",
            resource_id=uuid4(),
            action_details={"test": "data"},
            ip_address="127.0.0.1",
            user_agent="test-agent",
            status="success"
        )
        
        assert audit_entry.user_id == sample_user_id
        assert audit_entry.action_type == "investigation_created"
        assert audit_entry.resource_type == "investigation"
        assert audit_entry.status == "success"
        assert audit_entry.ip_address == "127.0.0.1"
    
    def test_log_action_with_error(self, db_session, sample_user_id):
        """Test logging an action with error"""
        service = AuditService(db_session)
        
        audit_entry = service.log_action(
            action_type="investigation_created",
            user_id=sample_user_id,
            status="error",
            error_message="Test error message"
        )
        
        assert audit_entry.status == "error"
        assert audit_entry.error_message == "Test error message"
    
    def test_get_audit_logs(self, db_session, sample_user_id):
        """Test getting audit logs"""
        service = AuditService(db_session)
        
        # Create audit entries
        service.log_action(
            action_type="investigation_created",
            user_id=sample_user_id,
            status="success"
        )
        service.log_action(
            action_type="evidence_added",
            user_id=sample_user_id,
            status="success"
        )
        
        logs = service.get_audit_logs(user_id=sample_user_id)
        
        assert len(logs) >= 2
    
    def test_get_audit_logs_filter_by_action_type(self, db_session, sample_user_id):
        """Test getting audit logs filtered by action type"""
        service = AuditService(db_session)
        
        # Create different action types
        service.log_action(
            action_type="investigation_created",
            user_id=sample_user_id,
            status="success"
        )
        service.log_action(
            action_type="evidence_added",
            user_id=sample_user_id,
            status="success"
        )
        
        logs = service.get_audit_logs(
            user_id=sample_user_id,
            action_type="investigation_created"
        )
        
        assert len(logs) >= 1
        assert all(log.action_type == "investigation_created" for log in logs)
    
    def test_get_audit_logs_filter_by_resource(self, db_session, sample_user_id):
        """Test getting audit logs filtered by resource"""
        service = AuditService(db_session)
        resource_id = uuid4()
        
        # Create audit entries
        service.log_action(
            action_type="investigation_updated",
            user_id=sample_user_id,
            resource_type="investigation",
            resource_id=resource_id,
            status="success"
        )
        service.log_action(
            action_type="evidence_added",
            user_id=sample_user_id,
            resource_type="evidence",
            resource_id=uuid4(),
            status="success"
        )
        
        logs = service.get_audit_logs(
            resource_type="investigation",
            resource_id=resource_id
        )
        
        assert len(logs) >= 1
        assert all(log.resource_type == "investigation" for log in logs)
        assert all(log.resource_id == resource_id for log in logs)
    
    def test_get_audit_logs_filter_by_status(self, db_session, sample_user_id):
        """Test getting audit logs filtered by status"""
        service = AuditService(db_session)
        
        # Create entries with different statuses
        service.log_action(
            action_type="test_action",
            user_id=sample_user_id,
            status="success"
        )
        service.log_action(
            action_type="test_action",
            user_id=sample_user_id,
            status="failed",
            error_message="Test error"
        )
        
        failed_logs = service.get_audit_logs(
            user_id=sample_user_id,
            status="failed"
        )
        
        assert len(failed_logs) >= 1
        assert all(log.status == "failed" for log in failed_logs)
    
    def test_get_audit_logs_with_date_range(self, db_session, sample_user_id):
        """Test getting audit logs with date range"""
        service = AuditService(db_session)
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # Create entry
        service.log_action(
            action_type="test_action",
            user_id=sample_user_id,
            status="success"
        )
        
        logs = service.get_audit_logs(
            user_id=sample_user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(logs) >= 1
        assert all(start_date <= log.created_at <= end_date for log in logs)
    
    def test_get_audit_logs_with_limit_offset(self, db_session, sample_user_id):
        """Test getting audit logs with limit and offset"""
        service = AuditService(db_session)
        
        # Create multiple entries
        for i in range(5):
            service.log_action(
                action_type=f"action_{i}",
                user_id=sample_user_id,
                status="success"
            )
        
        # Get first batch
        first_batch = service.get_audit_logs(
            user_id=sample_user_id,
            limit=2,
            offset=0
        )
        
        # Get second batch
        second_batch = service.get_audit_logs(
            user_id=sample_user_id,
            limit=2,
            offset=2
        )
        
        assert len(first_batch) <= 2
        assert len(second_batch) <= 2
        # Verify they're different
        first_ids = {log.log_id for log in first_batch}
        second_ids = {log.log_id for log in second_batch}
        assert first_ids.isdisjoint(second_ids)

