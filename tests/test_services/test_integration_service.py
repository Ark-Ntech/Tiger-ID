"""Tests for IntegrationService"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from backend.services.integration_service import IntegrationService
from backend.database.models import Facility, Evidence, BackgroundJob


class TestIntegrationService:
    """Tests for IntegrationService"""
    
    @pytest.fixture
    def mock_clients(self):
        """Create mock API clients"""
        usda_client = AsyncMock()
        cites_client = AsyncMock()
        usfws_client = AsyncMock()
        return {
            "usda": usda_client,
            "cites": cites_client,
            "usfws": usfws_client
        }
    
    def test_init(self, db_session, mock_clients):
        """Test service initialization"""
        service = IntegrationService(
            db_session,
            usda_client=mock_clients["usda"],
            cites_client=mock_clients["cites"],
            usfws_client=mock_clients["usfws"]
        )
        
        assert service.session == db_session
        assert service.usda_client == mock_clients["usda"]
        assert service.cites_client == mock_clients["cites"]
        assert service.usfws_client == mock_clients["usfws"]
    
    @pytest.mark.asyncio
    async def test_sync_facility_from_usda_create(self, db_session, mock_clients):
        """Test syncing facility from USDA (create new)"""
        service = IntegrationService(db_session, usda_client=mock_clients["usda"])
        
        # Mock USDA API response
        facility_data = {
            "exhibitor_name": "Test Facility",
            "state": "CA",
            "city": "Los Angeles",
            "address": "123 Main St",
            "tiger_count": 5
        }
        mock_clients["usda"].get_facility_details.return_value = facility_data
        
        # Sync facility
        facility = await service.sync_facility_from_usda("USDA-123")
        
        assert facility is not None
        assert facility.exhibitor_name == "Test Facility"
        assert facility.usda_license == "USDA-123"
        assert facility.state == "CA"
    
    @pytest.mark.asyncio
    async def test_sync_facility_from_usda_update(self, db_session, mock_clients):
        """Test syncing facility from USDA (update existing)"""
        from backend.services.facility_service import FacilityService
        
        # Create existing facility
        facility_service = FacilityService(db_session)
        existing_facility = facility_service.create_facility(
            exhibitor_name="Old Name",
            usda_license="USDA-123",
            state="NY"
        )
        
        service = IntegrationService(db_session, usda_client=mock_clients["usda"])
        
        # Mock USDA API response with updated data
        facility_data = {
            "exhibitor_name": "Updated Name",
            "state": "CA",
            "city": "Los Angeles",
            "address": "123 Main St",
            "tiger_count": 10
        }
        mock_clients["usda"].get_facility_details.return_value = facility_data
        
        # Sync facility
        facility = await service.sync_facility_from_usda("USDA-123")
        
        assert facility is not None
        assert facility.exhibitor_name == "Updated Name"
        assert facility.state == "CA"
    
    @pytest.mark.asyncio
    async def test_sync_facility_from_usda_no_client(self, db_session):
        """Test syncing facility when USDA client not available"""
        service = IntegrationService(db_session, usda_client=None)
        
        facility = await service.sync_facility_from_usda("USDA-123")
        
        assert facility is None
    
    @pytest.mark.asyncio
    async def test_sync_facility_from_usda_no_data(self, db_session, mock_clients):
        """Test syncing facility when USDA returns no data"""
        service = IntegrationService(db_session, usda_client=mock_clients["usda"])
        
        mock_clients["usda"].get_facility_details.return_value = None
        
        facility = await service.sync_facility_from_usda("USDA-123")
        
        assert facility is None
    
    @pytest.mark.asyncio
    async def test_sync_cites_records(self, db_session, mock_clients):
        """Test syncing CITES records"""
        service = IntegrationService(db_session, cites_client=mock_clients["cites"])
        
        # Mock CITES API response
        trade_records = [
            {
                "permit_number": "CITES-123",
                "species": "Panthera tigris",
                "export_country": "US",
                "import_country": "Canada"
            }
        ]
        mock_clients["cites"].get_trade_records.return_value = trade_records
        
        investigation_id = uuid4()
        result = await service.sync_cites_records(
            facility_id=uuid4(),
            investigation_id=investigation_id
        )
        
        assert result is not None
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_sync_usfws_permits(self, db_session, mock_clients):
        """Test syncing USFWS permits"""
        service = IntegrationService(db_session, usfws_client=mock_clients["usfws"])
        
        # Mock USFWS API response
        permits = [
            {
                "permit_number": "USFWS-123",
                "permit_type": "Import/Export",
                "species": "Panthera tigris"
            }
        ]
        mock_clients["usfws"].get_permits.return_value = permits
        
        investigation_id = uuid4()
        result = await service.sync_usfws_permits(
            facility_id=uuid4(),
            investigation_id=investigation_id
        )
        
        assert result is not None
        assert len(result) > 0

