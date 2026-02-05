"""Tests for AnalyticsService"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from backend.services.analytics_service import AnalyticsService
from backend.database.models import Investigation, Evidence


class TestAnalyticsService:
    """Tests for AnalyticsService"""
    
    def test_get_investigation_analytics(self, db_session, sample_user_id):
        """Test getting investigation analytics"""
        service = AnalyticsService(db_session)
        from backend.services.investigation_service import InvestigationService

        # Create investigations
        inv_service = InvestigationService(db_session)
        inv1 = inv_service.create_investigation(
            title="Investigation 1",
            created_by=sample_user_id,
            priority="high"
        )
        # Update status after creation
        inv1_updated = inv_service.update_investigation(inv1.investigation_id, status="active")
        assert inv1_updated is not None

        inv2 = inv_service.create_investigation(
            title="Investigation 2",
            created_by=sample_user_id,
            priority="medium"
        )
        # Update status after creation
        inv2_updated = inv_service.update_investigation(inv2.investigation_id, status="completed")
        assert inv2_updated is not None

        # Refresh the session to ensure updates are visible
        db_session.expire_all()

        analytics = service.get_investigation_analytics(user_id=sample_user_id)

        assert "total_investigations" in analytics
        assert "status_distribution" in analytics
        assert "priority_distribution" in analytics
        assert analytics["total_investigations"] >= 2
    
    def test_get_investigation_analytics_with_dates(self, db_session, sample_user_id):
        """Test getting investigation analytics with date filters"""
        service = AnalyticsService(db_session)
        from backend.services.investigation_service import InvestigationService
        
        inv_service = InvestigationService(db_session)
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        analytics = service.get_investigation_analytics(
            start_date=start_date,
            end_date=end_date,
            user_id=sample_user_id
        )
        
        assert "total_investigations" in analytics
        assert isinstance(analytics["total_investigations"], int)
    
    def test_get_evidence_analytics(self, db_session, sample_user_id):
        """Test getting evidence analytics"""
        service = AnalyticsService(db_session)
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
            relevance_score=0.9
        )
        inv_service.add_evidence(
            investigation.investigation_id,
            source_type="image",
            relevance_score=0.8
        )
        
        analytics = service.get_evidence_analytics(
            investigation_id=investigation.investigation_id
        )
        
        assert "total_evidence" in analytics
        assert "source_type_distribution" in analytics
        assert analytics["total_evidence"] >= 2
    
    def test_get_facility_analytics(self, db_session):
        """Test getting facility analytics"""
        service = AnalyticsService(db_session)
        from backend.services.facility_service import FacilityService
        import json

        facility_service = FacilityService(db_session)
        facility_service.create_facility(
            exhibitor_name="Facility 1",
            state="CA",
            tiger_count=5,
            social_media_links=None  # Pass None instead of dict for SQLite compatibility
        )
        facility_service.create_facility(
            exhibitor_name="Facility 2",
            state="NY",
            tiger_count=10,
            social_media_links=None  # Pass None instead of dict for SQLite compatibility
        )
        
        analytics = service.get_facility_analytics()
        
        assert "total_facilities" in analytics
        assert "state_distribution" in analytics
        assert analytics["total_facilities"] >= 2
    
    def test_get_agent_performance_analytics(self, db_session, sample_user_id):
        """Test getting agent performance analytics"""
        service = AnalyticsService(db_session)
        from backend.services.investigation_service import InvestigationService

        # Create investigation with steps
        inv_service = InvestigationService(db_session)
        inv = inv_service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id
        )

        # Add investigation steps
        inv_service.add_investigation_step(
            investigation_id=inv.investigation_id,
            step_type="research",
            agent_name="deep_research",
            status="completed"
        )
        inv_service.add_investigation_step(
            investigation_id=inv.investigation_id,
            step_type="analysis",
            agent_name="sequential_thinking",
            status="completed"
        )

        analytics = service.get_agent_performance_analytics(investigation_id=inv.investigation_id)

        assert isinstance(analytics, dict)
        assert "total_steps" in analytics
        assert "agent_activity" in analytics
        assert analytics["total_steps"] >= 2

