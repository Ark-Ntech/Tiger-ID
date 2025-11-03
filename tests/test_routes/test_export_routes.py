"""Tests for export routes"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# python-jose is now properly installed in requirements.txt

from backend.api.app import create_app
from backend.database.models import User


class TestExportRoutes:
    """Tests for export API routes"""
    
    def test_export_investigation_json(self, test_client, auth_headers, test_user, db_session):
        """Test exporting investigation as JSON"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        response = test_client.get(
            f"/api/v1/investigations/{investigation.investigation_id}/export/json",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["investigation_id"] == str(investigation.investigation_id)
        assert data["title"] == "Test Investigation"
    
    def test_export_investigation_markdown(self, test_client, auth_headers, test_user, db_session):
        """Test exporting investigation as Markdown"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        response = test_client.get(
            f"/api/v1/investigations/{investigation.investigation_id}/export/markdown",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "Test Investigation" in response.text
    
    def test_export_investigation_csv(self, test_client, auth_headers, test_user, db_session):
        """Test exporting investigation as CSV"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        response = test_client.get(
            f"/api/v1/investigations/{investigation.investigation_id}/export/csv?data_type=evidence",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

