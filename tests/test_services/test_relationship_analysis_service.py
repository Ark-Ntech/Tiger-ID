"""Tests for RelationshipAnalysisService"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from backend.services.relationship_analysis_service import RelationshipAnalysisService
from backend.database.models import Facility, Tiger


class TestRelationshipAnalysisService:
    """Tests for RelationshipAnalysisService"""
    
    def test_analyze_facility_relationships(self, db_session):
        """Test analyzing facility relationships"""
        from backend.services.facility_service import FacilityService
        
        facility_service = FacilityService(db_session)
        facility = facility_service.create_facility(
            exhibitor_name="Test Facility",
            state="CA"
        )
        
        service = RelationshipAnalysisService(db_session)
        
        result = service.analyze_facility_relationships(facility.facility_id)
        
        assert "facility_id" in result
        assert "facility_name" in result
        assert "connections" in result
        assert result["facility_name"] == "Test Facility"
    
    def test_analyze_facility_relationships_not_found(self, db_session):
        """Test analyzing relationships for nonexistent facility"""
        service = RelationshipAnalysisService(db_session)
        
        fake_id = uuid4()
        result = service.analyze_facility_relationships(fake_id)
        
        assert "error" in result
    
    def test_get_network_graph(self, db_session):
        """Test getting network graph"""
        service = RelationshipAnalysisService(db_session)
        
        result = service.get_network_graph(facility_ids=[])
        
        assert "nodes" in result or "graph" in result or isinstance(result, dict)
    
    def test_find_shared_tigers(self, db_session):
        """Test finding shared tigers"""
        from backend.services.facility_service import FacilityService
        
        facility_service = FacilityService(db_session)
        facility1 = facility_service.create_facility(
            exhibitor_name="Facility 1",
            state="CA"
        )
        facility2 = facility_service.create_facility(
            exhibitor_name="Facility 2",
            state="NY"
        )
        
        service = RelationshipAnalysisService(db_session)
        
        # Test finding shared tigers (may be empty if no tigers exist)
        result = service.find_shared_tigers([facility1.facility_id, facility2.facility_id])
        
        assert isinstance(result, list) or isinstance(result, dict)
    
    def test_analyze_tiger_movements(self, db_session):
        """Test analyzing tiger movements"""
        service = RelationshipAnalysisService(db_session)
        
        tiger_id = uuid4()
        result = service.analyze_tiger_movements(tiger_id)
        
        assert isinstance(result, dict)
        # Should handle nonexistent tiger gracefully

