"""Tests for investigation service"""

import pytest
from uuid import uuid4
from datetime import datetime

from backend.database import get_db_session, Investigation, InvestigationStep, Evidence
from backend.services.investigation_service import InvestigationService

# Note: db_session and sample_user_id fixtures are now in conftest.py

@pytest.fixture
def investigation_service(db_session):
    """Investigation service fixture"""
    return InvestigationService(db_session)


class TestInvestigationService:
    """Tests for InvestigationService"""
    
    def test_create_investigation(self, investigation_service, sample_user_id):
        """Test creating an investigation"""
        investigation = investigation_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id,
            description="Test description",
            priority="high"
        )
        
        assert investigation.title == "Test Investigation"
        assert investigation.created_by == sample_user_id
        assert investigation.status.value == "draft" if hasattr(investigation.status, 'value') else investigation.status == "draft"
        assert investigation.priority.value == "high" if hasattr(investigation.priority, 'value') else investigation.priority == "high"
        assert investigation.investigation_id is not None
    
    def test_get_investigation(self, investigation_service, sample_user_id):
        """Test getting an investigation"""
        investigation = investigation_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        retrieved = investigation_service.get_investigation(investigation.investigation_id)
        
        assert retrieved is not None
        assert retrieved.investigation_id == investigation.investigation_id
        assert retrieved.title == "Test Investigation"
    
    def test_get_investigations_with_filters(self, investigation_service, sample_user_id):
        """Test getting investigations with filters"""
        # Create multiple investigations
        investigation_service.create_investigation(
            title="High Priority",
            created_by=sample_user_id,
            priority="high"
        )
        investigation_service.create_investigation(
            title="Medium Priority",
            created_by=sample_user_id,
            priority="medium"
        )
        
        # Filter by priority
        high_priority = investigation_service.get_investigations(priority="high")
        assert len(high_priority) >= 1
        assert all((inv.priority.value if hasattr(inv.priority, 'value') else inv.priority) == "high" for inv in high_priority)
    
    def test_update_investigation(self, investigation_service, sample_user_id):
        """Test updating an investigation"""
        investigation = investigation_service.create_investigation(
            title="Original Title",
            created_by=sample_user_id
        )
        
        updated = investigation_service.update_investigation(
            investigation.investigation_id,
            title="Updated Title",
            status="active"  # Use 'active' instead of 'in_progress' which may not exist
        )
        
        assert updated.title == "Updated Title"
        assert updated.status.value == "active" if hasattr(updated.status, 'value') else updated.status == "active"
    
    def test_start_investigation(self, investigation_service, sample_user_id):
        """Test starting an investigation"""
        investigation = investigation_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        started = investigation_service.start_investigation(investigation.investigation_id)
        
        assert started.status.value == "active" if hasattr(started.status, 'value') else started.status == "active"
        assert started.started_at is not None
    
    def test_add_investigation_step(self, investigation_service, sample_user_id):
        """Test adding an investigation step"""
        investigation = investigation_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        step = investigation_service.add_investigation_step(
            investigation.investigation_id,
            step_type="research_started",
            agent_name="research_agent",
            status="in_progress",
            result={"test": "data"}
        )
        
        assert step.investigation_id == investigation.investigation_id
        assert step.step_type == "research_started"
        assert step.agent_name == "research_agent"
        assert step.result == {"test": "data"}
    
    def test_add_evidence(self, investigation_service, sample_user_id):
        """Test adding evidence to an investigation"""
        investigation = investigation_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        evidence = investigation_service.add_evidence(
            investigation.investigation_id,
            source_type="web_search",
            source_url="https://example.com",
            content={"key": "value"},
            extracted_text="Test text",
            relevance_score=0.9
        )
        
        assert evidence.investigation_id == investigation.investigation_id
        assert evidence.source_type.value == "web_search" if hasattr(evidence.source_type, 'value') else evidence.source_type == "web_search"
        assert evidence.relevance_score == 0.9
    
    def test_get_investigation_steps(self, investigation_service, sample_user_id):
        """Test getting investigation steps"""
        investigation = investigation_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        # Add multiple steps
        investigation_service.add_investigation_step(
            investigation.investigation_id,
            step_type="step1",
            status="completed"
        )
        investigation_service.add_investigation_step(
            investigation.investigation_id,
            step_type="step2",
            status="in_progress"
        )
        
        steps = investigation_service.get_investigation_steps(investigation.investigation_id)
        
        assert len(steps) == 2
        assert steps[0].step_type == "step1"
        assert steps[1].step_type == "step2"
    
    def test_get_investigation_evidence(self, investigation_service, sample_user_id):
        """Test getting investigation evidence"""
        investigation = investigation_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        # Add multiple evidence items
        investigation_service.add_evidence(
            investigation.investigation_id,
            source_type="image",
            relevance_score=0.8
        )
        investigation_service.add_evidence(
            investigation.investigation_id,
            source_type="document",
            relevance_score=0.9
        )
        
        evidence = investigation_service.get_investigation_evidence(investigation.investigation_id)
        
        assert len(evidence) == 2
        assert all(ev.investigation_id == investigation.investigation_id for ev in evidence)

