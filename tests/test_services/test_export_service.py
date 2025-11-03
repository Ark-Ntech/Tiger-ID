"""Tests for ExportService"""

import pytest
from uuid import uuid4

from backend.services.export_service import ExportService
from backend.database.models import Investigation, Evidence


class TestExportService:
    """Tests for ExportService"""
    
    def test_export_investigation_json(self, db_session, sample_user_id):
        """Test exporting investigation as JSON"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id,
            description="Test description"
        )
        
        service = ExportService(db_session)
        
        result = service.export_investigation_json(
            investigation.investigation_id,
            include_evidence=True,
            include_steps=True,
            include_metadata=True
        )
        
        assert "investigation_id" in result
        assert result["title"] == "Test Investigation"
        assert "evidence" in result
        assert "steps" in result
    
    def test_export_investigation_json_not_found(self, db_session):
        """Test exporting nonexistent investigation"""
        service = ExportService(db_session)
        
        fake_id = uuid4()
        result = service.export_investigation_json(fake_id)
        
        assert "error" in result
    
    def test_export_investigation_markdown(self, db_session, sample_user_id):
        """Test exporting investigation as Markdown"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id,
            description="Test description"
        )
        
        service = ExportService(db_session)
        
        result = service.export_investigation_markdown(
            investigation.investigation_id,
            include_evidence=True,
            include_steps=True
        )
        
        assert isinstance(result, str)
        assert "Test Investigation" in result
    
    def test_export_investigation_csv_evidence(self, db_session, sample_user_id):
        """Test exporting investigation evidence as CSV"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        # Add evidence
        inv_service.add_evidence(
            investigation.investigation_id,
            source_type="web_search",
            source_url="https://example.com",
            relevance_score=0.9
        )
        
        service = ExportService(db_session)
        
        result = service.export_investigation_csv(
            investigation.investigation_id,
            data_type="evidence"
        )
        
        assert isinstance(result, str)
        assert "evidence_id" in result or "source_type" in result
    
    def test_export_investigation_csv_steps(self, db_session, sample_user_id):
        """Test exporting investigation steps as CSV"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        # Add step
        inv_service.add_investigation_step(
            investigation.investigation_id,
            step_type="research_started",
            agent_name="research_agent",
            status="completed"
        )
        
        service = ExportService(db_session)
        
        result = service.export_investigation_csv(
            investigation.investigation_id,
            data_type="steps"
        )
        
        assert isinstance(result, str)

