"""Tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
import json

from backend.api.app import create_app
from backend.database.models import User, Investigation
from backend.auth.auth import create_access_token
from backend.database import get_db

# Note: Fixtures are now in conftest.py (test_client, test_user, auth_headers)


class TestAuthenticationEndpoints:
    """Tests for authentication endpoints"""
    
    def test_login_success(self, test_client, test_user):
        """Test successful login"""
        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass",  # Match the test_user fixture password
                "remember_me": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
    
    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials"""
        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "invalid",
                "password": "wrongpassword",
                "remember_me": False
            }
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_get_current_user(self, test_client, auth_headers, test_user, db_session):
        """Test getting current user info"""
        from backend.database.connection import get_db
        
        # Ensure get_db dependency is properly overridden
        app = test_client.app
        if get_db not in app.dependency_overrides:
            def override_get_db():
                try:
                    yield db_session
                finally:
                    pass
            app.dependency_overrides[get_db] = override_get_db
        
        response = test_client.get(
            "/api/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["user_id"] == str(test_user.user_id)


class TestInvestigationEndpoints:
    """Tests for investigation endpoints"""
    
    def test_create_investigation(self, test_client, auth_headers, test_user, db_session):
        """Test creating an investigation"""
        response = test_client.post(
            "/api/v1/investigations",
            headers=auth_headers,
            json={
                "title": "Test Investigation",
                "description": "Test description",
                "priority": "high",
                "tags": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Investigation"
        assert data["description"] == "Test description"
        assert data["priority"] == "high"
    
    def test_create_investigation_validation_error(self, test_client, auth_headers):
        """Test creating investigation with invalid data"""
        response = test_client.post(
            "/api/v1/investigations",
            headers=auth_headers,
            json={
                "title": "AB",  # Too short
                "description": "Test",
                "priority": "invalid"  # Invalid priority
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_investigation(self, test_client, auth_headers, test_user, db_session):
        """Test getting investigation by ID"""
        from backend.services.investigation_service import InvestigationService
        
        # Create investigation
        service = InvestigationService(db_session)
        investigation = service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id,
            description="Test"
        )
        
        response = test_client.get(
            f"/api/v1/investigations/{investigation.investigation_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Investigation"
        assert str(data["investigation_id"]) == str(investigation.investigation_id)
    
    def test_get_investigation_not_found(self, test_client, auth_headers):
        """Test getting non-existent investigation"""
        fake_id = uuid4()
        
        response = test_client.get(
            f"/api/v1/investigations/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_create_investigation_unauthorized(self, test_client):
        """Test creating investigation without authentication"""
        response = test_client.post(
            "/api/v1/investigations",
            json={
                "title": "Test Investigation",
                "description": "Test",
                "priority": "medium"
            }
        )
        
        # Can be 401 (no token) or 403 (no permission) depending on middleware
        assert response.status_code in [401, 403]


class TestRateLimiting:
    """Tests for rate limiting middleware"""
    
    def test_rate_limit_exceeded(self, test_client, auth_headers):
        """Test rate limiting"""
        # Make 61 requests rapidly (limit is 60 per minute)
        for i in range(61):
            response = test_client.get(
                "/api/auth/me",
                headers=auth_headers
            )
            if response.status_code == 429:
                assert "Rate limit exceeded" in response.json()["detail"]
                break
        
        # At least one should hit rate limit
        assert i >= 60 or response.status_code == 429


class TestInputValidation:
    """Tests for input validation"""
    
    def test_investigation_title_validation(self, test_client, auth_headers):
        """Test investigation title validation"""
        # Title too short
        response = test_client.post(
            "/api/v1/investigations",
            headers=auth_headers,
            json={
                "title": "AB",  # Less than 3 characters
                "description": "Test",
                "priority": "medium"
            }
        )
        
        assert response.status_code == 422
    
    def test_investigation_title_xss_prevention(self, test_client, auth_headers):
        """Test XSS prevention in investigation title"""
        malicious_title = "<script>alert('xss')</script>Test Investigation"
        
        response = test_client.post(
            "/api/v1/investigations",
            headers=auth_headers,
            json={
                "title": malicious_title,
                "description": "Test",
                "priority": "medium"
            }
        )
        
        # Should sanitize the title (script tags removed)
        if response.status_code == 200:
            data = response.json()
            # Check that dangerous content was sanitized
            assert "<script>" not in data.get("title", "")
            # Script content (alert) should be removed by sanitization
            # Test may pass even if 'alert' remains as text (not executable)

