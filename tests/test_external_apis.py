"""Tests for external API integrations"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from backend.services.external_apis.usda_client import USDAClient
from backend.services.external_apis.cites_client import CITESClient
from backend.services.external_apis.usfws_client import USFWSClient
from backend.services.external_apis.atrw_dataset import ATRWDatasetManager
from backend.services.integration_service import IntegrationService
from backend.database.connection import SessionLocal
from backend.database.models import Facility, Evidence, Investigation


@pytest.fixture
def mock_usda_client():
    """Mock USDA client"""
    client = USDAClient(api_key="test_key")
    client._request = AsyncMock(return_value={"results": []})
    return client


@pytest.fixture
def mock_cites_client():
    """Mock CITES client"""
    client = CITESClient(api_key="test_key")
    client._request = AsyncMock(return_value={"results": []})
    return client


@pytest.fixture
def mock_usfws_client():
    """Mock USFWS client"""
    client = USFWSClient(api_key="test_key")
    client._request = AsyncMock(return_value={"results": []})
    return client


@pytest.fixture
def db_session():
    """Database session fixture"""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def integration_service(db_session, mock_usda_client, mock_cites_client, mock_usfws_client):
    """Integration service fixture"""
    return IntegrationService(
        session=db_session,
        usda_client=mock_usda_client,
        cites_client=mock_cites_client,
        usfws_client=mock_usfws_client
    )


class TestUSDAClient:
    """Tests for USDA client"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_usda_client):
        """Test USDA health check"""
        mock_usda_client._request = AsyncMock(
            side_effect=Exception("Not implemented")
        )
        result = await mock_usda_client.health_check()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_search_facilities(self, mock_usda_client):
        """Test facility search"""
        mock_usda_client._request = AsyncMock(return_value={
            "results": [
                {
                    "license_number": "USDA-123",
                    "exhibitor_name": "Test Zoo",
                    "state": "CA",
                    "city": "Los Angeles"
                }
            ]
        })
        
        results = await mock_usda_client.search_facilities(
            license_number="USDA-123"
        )
        assert len(results) > 0
        assert results[0]["license_number"] == "USDA-123"
    
    @pytest.mark.asyncio
    async def test_get_facility_details(self, mock_usda_client):
        """Test get facility details"""
        mock_usda_client._request = AsyncMock(return_value={
            "license_number": "USDA-123",
            "exhibitor_name": "Test Zoo",
            "state": "CA",
            "tiger_count": 5
        })
        
        result = await mock_usda_client.get_facility_details("USDA-123")
        assert result is not None
        assert result["license_number"] == "USDA-123"
        assert result["tiger_count"] == 5


class TestCITESClient:
    """Tests for CITES client"""
    
    @pytest.mark.asyncio
    async def test_search_trade_records(self, mock_cites_client):
        """Test trade record search"""
        mock_cites_client._request = AsyncMock(return_value={
            "results": [
                {
                    "record_id": "CITES-001",
                    "species": "Panthera tigris",
                    "country_origin": "US",
                    "country_destination": "MX",
                    "year": 2023
                }
            ]
        })
        
        results = await mock_cites_client.search_trade_records(
            species="Panthera tigris",
            year=2023
        )
        assert len(results) > 0
        assert results[0]["species"] == "Panthera tigris"
    
    @pytest.mark.asyncio
    async def test_get_tiger_trade_records(self, mock_cites_client):
        """Test tiger-specific trade records"""
        mock_cites_client.search_trade_records = AsyncMock(return_value=[
            {"record_id": "CITES-001", "species": "Panthera tigris"}
        ])
        
        results = await mock_cites_client.get_tiger_trade_records(year=2023)
        assert len(results) > 0


class TestUSFWSClient:
    """Tests for USFWS client"""
    
    @pytest.mark.asyncio
    async def test_search_permits(self, mock_usfws_client):
        """Test permit search"""
        mock_usfws_client._request = AsyncMock(return_value={
            "results": [
                {
                    "permit_number": "USFWS-123",
                    "applicant_name": "Test Importer",
                    "permit_type": "Import",
                    "species": "Panthera tigris"
                }
            ]
        })
        
        results = await mock_usfws_client.search_permits(
            species="Panthera tigris"
        )
        assert len(results) > 0
        assert results[0]["species"] == "Panthera tigris"
    
    @pytest.mark.asyncio
    async def test_get_tiger_permit_records(self, mock_usfws_client):
        """Test tiger-specific permit records"""
        mock_usfws_client.search_permits = AsyncMock(return_value=[
            {"permit_number": "USFWS-123", "species": "Panthera tigris"}
        ])
        
        results = await mock_usfws_client.get_tiger_permit_records()
        assert len(results) > 0


class TestATRWDatasetManager:
    """Tests for ATRW dataset manager"""
    
    def test_init(self, tmp_path):
        """Test dataset manager initialization"""
        manager = ATRWDatasetManager(dataset_dir=tmp_path / "atrw")
        assert manager.dataset_dir.exists()
        assert manager.images_dir.exists()
        assert manager.annotations_dir.exists()
    
    @pytest.mark.asyncio
    async def test_check_dataset_exists(self, tmp_path):
        """Test dataset existence check"""
        manager = ATRWDatasetManager(dataset_dir=tmp_path / "atrw")
        
        # Create required files/directories
        (manager.dataset_dir / "README.md").touch()
        manager.images_dir.mkdir(exist_ok=True)
        manager.annotations_dir.mkdir(exist_ok=True)
        
        exists = await manager.check_dataset_exists()
        assert exists is True
    
    def test_get_dataset_info(self):
        """Test dataset info retrieval"""
        manager = ATRWDatasetManager(dataset_dir="./data/models/atrw")
        info = manager.get_dataset_info()
        
        assert info["name"] == "ATRW"
        assert info["num_tigers"] == 92
        assert "paper_url" in info


class TestIntegrationService:
    """Tests for integration service"""
    
    @pytest.mark.asyncio
    async def test_sync_facility_from_usda(
        self,
        integration_service,
        mock_usda_client
    ):
        """Test facility sync from USDA"""
        # Mock USDA responses
        mock_usda_client.get_facility_details = AsyncMock(return_value={
            "exhibitor_name": "Test Zoo",
            "state": "CA",
            "city": "Los Angeles",
            "address": "123 Zoo St",
            "tiger_count": 5
        })
        mock_usda_client.get_inspection_reports = AsyncMock(return_value=[])
        
        integration_service.usda_client = mock_usda_client
        
        facility = await integration_service.sync_facility_from_usda(
            license_number="USDA-123"
        )
        
        assert facility is not None
        assert facility.exhibitor_name == "Test Zoo"
        assert facility.usda_license == "USDA-123"
    
    @pytest.mark.asyncio
    async def test_sync_cites_trade_records(
        self,
        integration_service,
        mock_cites_client,
        db_session
    ):
        """Test CITES trade record sync"""
        from uuid import uuid4
        
        # Create test investigation
        investigation = Investigation(
            title="Test Investigation",
            description="Test",
            created_by=uuid4(),
            status="draft"
        )
        db_session.add(investigation)
        db_session.commit()
        
        # Mock CITES responses
        mock_cites_client.get_tiger_trade_records = AsyncMock(return_value=[
            {
                "record_id": "CITES-001",
                "species": "Panthera tigris",
                "country_origin": "US",
                "country_destination": "MX",
                "year": 2023
            }
        ])
        
        integration_service.cites_client = mock_cites_client
        
        records = await integration_service.sync_cites_trade_records(
            investigation_id=investigation.investigation_id,
            year=2023
        )
        
        assert len(records) > 0
        
        # Check evidence was created
        evidence = db_session.query(Evidence).filter(
            Evidence.investigation_id == investigation.investigation_id
        ).all()
        assert len(evidence) > 0
    
    @pytest.mark.asyncio
    async def test_sync_usfws_permits(
        self,
        integration_service,
        mock_usfws_client,
        db_session
    ):
        """Test USFWS permit sync"""
        from uuid import uuid4
        
        # Create test investigation
        investigation = Investigation(
            title="Test Investigation",
            description="Test",
            created_by=uuid4(),
            status="draft"
        )
        db_session.add(investigation)
        db_session.commit()
        
        # Mock USFWS responses
        mock_usfws_client.get_tiger_permit_records = AsyncMock(return_value=[
            {
                "permit_number": "USFWS-123",
                "applicant_name": "Test Importer",
                "permit_type": "Import",
                "species": "Panthera tigris"
            }
        ])
        
        integration_service.usfws_client = mock_usfws_client
        
        permits = await integration_service.sync_usfws_permits(
            investigation_id=investigation.investigation_id
        )
        
        assert len(permits) > 0
        
        # Check evidence was created
        evidence = db_session.query(Evidence).filter(
            Evidence.investigation_id == investigation.investigation_id
        ).all()
        assert len(evidence) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

