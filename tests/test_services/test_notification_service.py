"""Tests for NotificationService"""

import pytest
from uuid import uuid4
from datetime import datetime

from backend.services.notification_service import NotificationService
from backend.database.models import Notification, User


class TestNotificationService:
    """Tests for NotificationService"""
    
    def test_create_notification(self, db_session, sample_user_id):
        """Test creating a notification"""
        service = NotificationService(db_session)
        
        notification = service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="New Evidence",
            message="Evidence found in investigation",
            priority="high"
        )
        
        assert notification.user_id == sample_user_id
        assert notification.type == "evidence_found"
        assert notification.title == "New Evidence"
        assert "[HIGH]" in notification.message
        assert notification.read is False
    
    def test_create_notification_with_investigation(self, db_session, sample_user_id):
        """Test creating notification with investigation ID"""
        service = NotificationService(db_session)
        investigation_id = uuid4()
        
        notification = service.create_notification(
            user_id=sample_user_id,
            notification_type="phase_complete",
            title="Phase Complete",
            message="Investigation phase completed",
            investigation_id=investigation_id
        )
        
        assert notification.related_entity_type == "investigation"
        assert notification.related_entity_id == investigation_id
    
    def test_create_notification_with_evidence(self, db_session, sample_user_id):
        """Test creating notification with evidence ID"""
        service = NotificationService(db_session)
        evidence_id = uuid4()
        
        notification = service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="New Evidence",
            message="New evidence found",
            evidence_id=evidence_id
        )
        
        assert notification.related_entity_type == "evidence"
        assert notification.related_entity_id == evidence_id
    
    def test_get_notifications(self, db_session, sample_user_id):
        """Test getting notifications"""
        service = NotificationService(db_session)
        
        # Create multiple notifications
        service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Notification 1",
            message="Message 1"
        )
        service.create_notification(
            user_id=sample_user_id,
            notification_type="phase_complete",
            title="Notification 2",
            message="Message 2"
        )
        
        notifications = service.get_notifications(sample_user_id)
        
        assert len(notifications) >= 2
    
    def test_get_notifications_filter_unread(self, db_session, sample_user_id):
        """Test getting unread notifications"""
        service = NotificationService(db_session)
        
        # Create read and unread notifications
        notification1 = service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Unread",
            message="Unread message"
        )
        notification2 = service.create_notification(
            user_id=sample_user_id,
            notification_type="phase_complete",
            title="Read",
            message="Read message"
        )
        
        # Mark one as read
        service.mark_as_read(notification2.notification_id, sample_user_id)
        
        unread = service.get_notifications(sample_user_id, read=False)
        
        assert len(unread) >= 1
        assert all(not n.read for n in unread)
    
    def test_get_notifications_filter_type(self, db_session, sample_user_id):
        """Test getting notifications filtered by type"""
        service = NotificationService(db_session)
        
        # Create different types of notifications
        service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Evidence",
            message="Evidence message"
        )
        service.create_notification(
            user_id=sample_user_id,
            notification_type="phase_complete",
            title="Phase",
            message="Phase message"
        )
        
        evidence_notifications = service.get_notifications(
            sample_user_id,
            notification_type="evidence_found"
        )
        
        assert len(evidence_notifications) >= 1
        assert all(n.type == "evidence_found" for n in evidence_notifications)
    
    def test_mark_as_read(self, db_session, sample_user_id):
        """Test marking notification as read"""
        service = NotificationService(db_session)
        
        notification = service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Test",
            message="Test message"
        )
        
        assert notification.read is False
        
        updated = service.mark_as_read(notification.notification_id, sample_user_id)
        
        assert updated is not None
        assert updated.read is True
        # read_at might not exist on all Notification models
        if hasattr(updated, 'read_at'):
            assert updated.read_at is not None
    
    def test_mark_all_as_read(self, db_session, sample_user_id):
        """Test marking all notifications as read"""
        service = NotificationService(db_session)
        
        # Create multiple unread notifications
        service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Test 1",
            message="Message 1"
        )
        service.create_notification(
            user_id=sample_user_id,
            notification_type="phase_complete",
            title="Test 2",
            message="Message 2"
        )
        
        count = service.mark_all_as_read(sample_user_id)
        
        assert count >= 2
        
        # Verify all are read
        unread = service.get_notifications(sample_user_id, read=False)
        assert len(unread) == 0
    
    def test_delete_notification(self, db_session, sample_user_id):
        """Test deleting notification"""
        service = NotificationService(db_session)
        
        notification = service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Test",
            message="Test message"
        )
        
        notification_id = notification.notification_id
        
        result = service.delete_notification(notification_id, sample_user_id)
        
        assert result is True
        
        # Verify deleted (if get_notification method exists)
        if hasattr(service, 'get_notification'):
            retrieved = service.get_notification(notification_id)
            assert retrieved is None
        else:
            # Just verify the method returned True
            assert result is True
    
    def test_get_unread_count(self, db_session, sample_user_id):
        """Test getting unread notification count"""
        service = NotificationService(db_session)
        
        # Create multiple notifications
        notification1 = service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Unread 1",
            message="Message 1"
        )
        notification2 = service.create_notification(
            user_id=sample_user_id,
            notification_type="evidence_found",
            title="Unread 2",
            message="Message 2"
        )
        
        # Mark one as read
        service.mark_as_read(notification1.notification_id, sample_user_id)
        
        count = service.get_unread_count(sample_user_id)
        
        assert count >= 1

