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
        inv_service.create_investigation(
            title="Investigation 1",
            created_by=sample_user_id,
            status="active",
            priority="high"
        )
        inv_service.create_investigation(
            title="Investigation 2",
            created_by=sample_user_id,
            status="completed",
            priority="medium"
        )
        
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
        
        facility_service = FacilityService(db_session)
        facility_service.create_facility(
            exhibitor_name="Facility 1",
            state="CA",
            tiger_count=5
        )
        facility_service.create_facility(
            exhibitor_name="Facility 2",
            state="NY",
            tiger_count=10
        )
        
        analytics = service.get_facility_analytics()
        
        assert "total_facilities" in analytics
        assert "state_distribution" in analytics
        assert analytics["total_facilities"] >= 2
    
    def test_get_user_activity_analytics(self, db_session, sample_user_id):
        """Test getting user activity analytics"""
        service = AnalyticsService(db_session)
        
        analytics = service.get_user_activity_analytics(user_id=sample_user_id)
        
        assert isinstance(analytics, dict)
        # Should return analytics even if empty

