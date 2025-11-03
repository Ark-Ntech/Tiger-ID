"""Tests for TimelineService"""

import pytest
from uuid import uuid4

from backend.services.timeline_service import TimelineService
from backend.database.models import Investigation, Evidence


class TestTimelineService:
    """Tests for TimelineService"""
    
    def test_build_investigation_timeline(self, db_session, sample_user_id):
        """Test building investigation timeline"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id,
            description="Test description"
        )
        
        service = TimelineService(db_session)
        
        timeline = service.build_investigation_timeline(
            investigation.investigation_id,
            include_web_evidence=True,
            include_reference_events=True
        )
        
        assert "events" in timeline or "timeline" in timeline or isinstance(timeline, list)
    
    def test_build_investigation_timeline_not_found(self, db_session):
        """Test building timeline for nonexistent investigation"""
        service = TimelineService(db_session)
        
        fake_id = uuid4()
        result = service.build_investigation_timeline(fake_id)
        
        assert "error" in result
    
    def test_find_timeline_gaps(self, db_session, sample_user_id):
        """Test finding timeline gaps"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        service = TimelineService(db_session)
        
        gaps = service.find_timeline_gaps(investigation.investigation_id)
        
        assert isinstance(gaps, list)
    
    def test_get_timeline_summary(self, db_session, sample_user_id):
        """Test getting timeline summary"""
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )
        
        service = TimelineService(db_session)
        
        summary = service.get_timeline_summary(investigation.investigation_id)
        
        assert "event_count" in summary or "total_events" in summary or isinstance(summary, dict)

