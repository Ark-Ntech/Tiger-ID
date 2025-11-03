"""Tests for TemplateService"""

import pytest
from uuid import uuid4

from backend.services.template_service import TemplateService
from backend.database.models import InvestigationTemplate


class TestTemplateService:
    """Tests for TemplateService"""
    
    def test_create_template(self, db_session, sample_user_id):
        """Test creating a template"""
        service = TemplateService(db_session)
        
        template = service.create_template(
            name="Test Template",
            description="Test description",
            workflow_steps=[{"step": "research", "agent": "research_agent"}],
            default_agents=["research_agent", "analysis_agent"],
            created_by=sample_user_id
        )
        
        assert template.name == "Test Template"
        assert template.description == "Test description"
        assert len(template.workflow_steps) == 1
        assert len(template.default_agents) == 2
    
    def test_get_template(self, db_session, sample_user_id):
        """Test getting template by ID"""
        service = TemplateService(db_session)
        
        created = service.create_template(
            name="Test Template",
            description="Test",
            workflow_steps=[],
            default_agents=[],
            created_by=sample_user_id
        )
        
        retrieved = service.get_template(created.template_id)
        
        assert retrieved is not None
        assert retrieved.template_id == created.template_id
        assert retrieved.name == "Test Template"
    
    def test_get_templates(self, db_session, sample_user_id):
        """Test getting templates"""
        service = TemplateService(db_session)
        
        # Create multiple templates
        service.create_template(
            name="Template 1",
            description="Template 1",
            workflow_steps=[],
            default_agents=[],
            created_by=sample_user_id
        )
        service.create_template(
            name="Template 2",
            description="Template 2",
            workflow_steps=[],
            default_agents=[],
            created_by=sample_user_id
        )
        
        templates = service.get_templates(created_by=sample_user_id)
        
        assert len(templates) >= 2
    
    def test_update_template(self, db_session, sample_user_id):
        """Test updating template"""
        service = TemplateService(db_session)
        
        template = service.create_template(
            name="Original Name",
            description="Original",
            workflow_steps=[],
            default_agents=[],
            created_by=sample_user_id
        )
        
        updated = service.update_template(
            template.template_id,
            name="Updated Name",
            description="Updated"
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated"
    
    def test_delete_template(self, db_session, sample_user_id):
        """Test deleting template"""
        service = TemplateService(db_session)
        
        template = service.create_template(
            name="To Delete",
            description="Delete me",
            workflow_steps=[],
            default_agents=[],
            created_by=sample_user_id
        )
        
        template_id = template.template_id
        
        result = service.delete_template(template_id)
        
        assert result is True
        
        # Verify deleted
        retrieved = service.get_template(template_id)
        assert retrieved is None
    
    def test_apply_template(self, db_session, sample_user_id):
        """Test applying template to investigation"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        template_service = TemplateService(db_session)
        template = template_service.create_template(
            name="Test Template",
            description="Test",
            workflow_steps=[{"step": "research"}],
            default_agents=["research_agent"],
            created_by=sample_user_id
        )
        
        result = template_service.apply_template(template.template_id, investigation.investigation_id)
        
        assert result is not None
        assert "investigation_id" in result or "applied" in result

