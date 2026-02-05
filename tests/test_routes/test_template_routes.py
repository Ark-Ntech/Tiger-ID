"""Tests for template routes"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# python-jose is now properly installed in requirements.txt

from backend.api.app import create_app
from backend.database.models import User


class TestTemplateRoutes:
    """Tests for template API routes"""
    
    def test_create_template(self, test_client, auth_headers, test_user):
        """Test creating a template"""
        response = test_client.post(
            "/api/v1/templates",
            headers=auth_headers,
            json={
                "name": "Test Template",
                "description": "Test description",
                "workflow_steps": [{"step": "research"}],
                "default_agents": ["research_agent"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Template"
    
    def test_get_templates(self, test_client, auth_headers):
        """Test getting templates"""
        response = test_client.get(
            "/api/v1/templates",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)
    
    def test_apply_template(self, test_client, auth_headers, test_user, db_session):
        """Test applying template to investigation"""
        from backend.services.investigation_service import InvestigationService
        from backend.services.template_service import TemplateService

        # Create investigation and template
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )

        template_service = TemplateService(db_session)
        template = template_service.create_template(
            name="Test Template",
            description="Test",
            workflow_steps=[],
            default_agents=[],
            created_by=test_user.user_id
        )

        response = test_client.post(
            f"/api/v1/templates/{template.template_id}/apply?investigation_id={investigation.investigation_id}",
            headers=auth_headers
        )

        assert response.status_code == 200

