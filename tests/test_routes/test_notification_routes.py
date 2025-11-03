"""Tests for notification routes"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# python-jose is now properly installed in requirements.txt

from backend.api.app import create_app
from backend.database.models import User


class TestNotificationRoutes:
    """Tests for notification API routes"""
    
    def test_get_notifications(self, test_client, auth_headers, test_user):
        """Test getting notifications"""
        response = test_client.get(
            "/api/v1/notifications",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)
    
    def test_get_unread_count(self, test_client, auth_headers):
        """Test getting unread notification count"""
        response = test_client.get(
            "/api/v1/notifications/unread/count",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data or "unread_count" in data
    
    def test_mark_notification_read(self, test_client, auth_headers, test_user, db_session):
        """Test marking notification as read"""
        from backend.services.notification_service import NotificationService
        
        notification_service = NotificationService(db_session)
        notification = notification_service.create_notification(
            user_id=test_user.user_id,
            notification_type="test",
            title="Test",
            message="Test message"
        )
        
        response = test_client.post(
            f"/api/v1/notifications/{notification.notification_id}/read",
            headers=auth_headers
        )
        
        assert response.status_code == 200

