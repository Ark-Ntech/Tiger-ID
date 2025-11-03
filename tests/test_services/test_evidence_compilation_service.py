"""Tests for EvidenceCompilationService"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from backend.services.evidence_compilation_service import EvidenceCompilationService
from backend.database.models import Evidence, Investigation


class TestEvidenceCompilationService:
    """Tests for EvidenceCompilationService"""
    
    @pytest.mark.asyncio
    async def test_compile_evidence_from_web(self, db_session):
        """Test compiling evidence from web source"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=uuid4()
        )
        
        service = EvidenceCompilationService(db_session)
        
        # Mock data extraction
        with patch.object(service.data_extraction, 'extract_structured_data') as mock_extract:
            mock_extract.return_value = {
                "extracted": {
                    "title": "Test Evidence",
                    "content": "Test content"
                }
            }
            
            result = await service.compile_evidence_from_web(
                investigation.investigation_id,
                source_url="https://example.com",
                source_type="web_search"
            )
            
            assert "evidence_id" in result or "evidence" in result
    
    @pytest.mark.asyncio
    async def test_compile_evidence_batch(self, db_session):
        """Test compiling evidence from multiple sources"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=uuid4()
        )
        
        service = EvidenceCompilationService(db_session)
        
        source_urls = [
            "https://example.com/1",
            "https://example.com/2"
        ]
        
        with patch.object(service.data_extraction, 'extract_structured_data') as mock_extract:
            mock_extract.return_value = {
                "extracted": {"title": "Test", "content": "Content"}
            }
            
            result = await service.compile_evidence_batch(
                investigation.investigation_id,
                source_urls
            )
            
            assert isinstance(result, list) or isinstance(result, dict)
    
    def test_score_evidence(self):
        """Test scoring evidence"""
        service = EvidenceCompilationService()
        
        extracted_data = {
            "title": "Tiger Facility Investigation",
            "content": "Facility with suspicious activity"
        }
        
        score = service._score_evidence(
            source_url="https://example.com",
            extracted_data=extracted_data,
            source_type="web_search"
        )
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_get_evidence_summary(self, db_session):
        """Test getting evidence summary"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=uuid4()
        )
        
        # Add evidence
        inv_service.add_evidence(
            investigation.investigation_id,
            source_type="web_search",
            source_url="https://example.com",
            relevance_score=0.9
        )
        
        service = EvidenceCompilationService(db_session)
        
        summary = service.get_evidence_summary(investigation.investigation_id)
        
        assert "total_evidence" in summary or "evidence_count" in summary
        assert isinstance(summary, dict)

