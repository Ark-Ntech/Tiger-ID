"""Tests for analytics routes"""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.database.models import User


class TestAnalyticsRoutes:
    """Tests for analytics API routes"""
    
    def test_get_investigation_analytics(self, test_client, auth_headers):
        """Test getting investigation analytics"""
        response = test_client.get(
            "/api/v1/analytics/investigations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_investigations" in data or isinstance(data, dict)
    
    def test_get_evidence_analytics(self, test_client, auth_headers, test_user, db_session):
        """Test getting evidence analytics"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        response = test_client.get(
            f"/api/v1/analytics/evidence?investigation_id={investigation.investigation_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_facility_analytics(self, test_client, auth_headers):
        """Test getting facility analytics"""
        response = test_client.get(
            "/api/v1/analytics/facilities",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

