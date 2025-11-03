"""Tests for FacilityService"""

import pytest
from uuid import uuid4

from backend.services.facility_service import FacilityService
from backend.database.models import Facility


class TestFacilityService:
    """Tests for FacilityService"""
    
    def test_create_facility(self, db_session):
        """Test creating a facility"""
        service = FacilityService(db_session)
        
        facility = service.create_facility(
            exhibitor_name="Test Facility",
            usda_license="USDA-123",
            state="CA",
            city="Los Angeles",
            tiger_count=5
        )
        
        assert facility.exhibitor_name == "Test Facility"
        assert facility.usda_license == "USDA-123"
        assert facility.state == "CA"
        assert facility.city == "Los Angeles"
        assert facility.tiger_count == 5
        assert facility.facility_id is not None
    
    def test_get_facility(self, db_session):
        """Test getting facility by ID"""
        service = FacilityService(db_session)
        
        # Create facility
        facility = service.create_facility(
            exhibitor_name="Test Facility",
            usda_license="USDA-123"
        )
        
        # Retrieve facility
        retrieved = service.get_facility(facility.facility_id)
        
        assert retrieved is not None
        assert retrieved.facility_id == facility.facility_id
        assert retrieved.exhibitor_name == "Test Facility"
    
    def test_get_facility_by_license(self, db_session):
        """Test getting facility by USDA license"""
        service = FacilityService(db_session)
        
        # Create facility
        facility = service.create_facility(
            exhibitor_name="Test Facility",
            usda_license="USDA-456"
        )
        
        # Retrieve by license
        retrieved = service.get_facility_by_license("USDA-456")
        
        assert retrieved is not None
        assert retrieved.usda_license == "USDA-456"
        assert retrieved.facility_id == facility.facility_id
    
    def test_get_facilities_no_filters(self, db_session):
        """Test getting all facilities"""
        service = FacilityService(db_session)
        
        # Create multiple facilities
        service.create_facility(exhibitor_name="Facility 1", state="CA")
        service.create_facility(exhibitor_name="Facility 2", state="NY")
        
        facilities = service.get_facilities()
        
        assert len(facilities) >= 2
    
    def test_get_facilities_filter_by_state(self, db_session):
        """Test getting facilities filtered by state"""
        service = FacilityService(db_session)
        
        # Create facilities in different states
        service.create_facility(exhibitor_name="CA Facility", state="CA")
        service.create_facility(exhibitor_name="NY Facility", state="NY")
        
        ca_facilities = service.get_facilities(state="CA")
        
        assert len(ca_facilities) >= 1
        assert all(f.state == "CA" for f in ca_facilities)
    
    def test_get_facilities_search_query(self, db_session):
        """Test getting facilities with search query"""
        service = FacilityService(db_session)
        
        # Create facilities
        service.create_facility(exhibitor_name="Test Zoo", usda_license="USDA-123")
        service.create_facility(exhibitor_name="Another Facility", usda_license="USDA-456")
        
        # Search by name
        results = service.get_facilities(search_query="Zoo")
        
        assert len(results) >= 1
        assert any("Zoo" in f.exhibitor_name for f in results)
        
        # Search by license
        results = service.get_facilities(search_query="USDA-123")
        
        assert len(results) >= 1
        assert any(f.usda_license == "USDA-123" for f in results)
    
    def test_get_facilities_with_limit_offset(self, db_session):
        """Test getting facilities with limit and offset"""
        service = FacilityService(db_session)
        
        # Create multiple facilities
        for i in range(5):
            service.create_facility(exhibitor_name=f"Facility {i}")
        
        # Get first 2
        first_batch = service.get_facilities(limit=2, offset=0)
        
        # Get next 2
        second_batch = service.get_facilities(limit=2, offset=2)
        
        assert len(first_batch) <= 2
        assert len(second_batch) <= 2
        # Verify they're different
        first_ids = {f.facility_id for f in first_batch}
        second_ids = {f.facility_id for f in second_batch}
        assert first_ids.isdisjoint(second_ids)
    
    def test_update_facility(self, db_session):
        """Test updating a facility"""
        service = FacilityService(db_session)
        
        # Create facility
        facility = service.create_facility(
            exhibitor_name="Original Name",
            state="CA"
        )
        
        # Update facility
        updated = service.update_facility(
            facility.facility_id,
            exhibitor_name="Updated Name",
            tiger_count=10
        )
        
        assert updated is not None
        assert updated.exhibitor_name == "Updated Name"
        assert updated.tiger_count == 10
        assert updated.state == "CA"  # Unchanged field
    
    def test_update_facility_nonexistent(self, db_session):
        """Test updating nonexistent facility"""
        service = FacilityService(db_session)
        
        fake_id = uuid4()
        result = service.update_facility(fake_id, exhibitor_name="New Name")
        
        assert result is None
    
    def test_create_facility_with_social_media(self, db_session):
        """Test creating facility with social media links"""
        service = FacilityService(db_session)
        
        social_media = {
            "facebook": "https://facebook.com/test",
            "instagram": "@testfacility"
        }
        
        facility = service.create_facility(
            exhibitor_name="Test Facility",
            social_media_links=social_media
        )
        
        assert facility.social_media_links == social_media
    
    def test_get_facility_nonexistent(self, db_session):
        """Test getting nonexistent facility"""
        service = FacilityService(db_session)
        
        fake_id = uuid4()
        result = service.get_facility(fake_id)
        
        assert result is None

