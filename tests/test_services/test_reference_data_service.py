"""Tests for ReferenceDataService"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.services.reference_data_service import ReferenceDataService


class TestReferenceDataService:
    """Tests for ReferenceDataService"""
    
    def test_find_matching_facilities(self, db_session):
        """Test finding matching facilities"""
        service = ReferenceDataService(db_session)
        
        result = service.find_matching_facilities(name="Test Facility")
        
        assert isinstance(result, list)
    
    def test_sync_reference_data(self, db_session):
        """Test syncing reference data"""
        service = ReferenceDataService(db_session)
        
        result = service.sync_reference_data()
        
        assert "synced" in result or "count" in result or isinstance(result, dict)

