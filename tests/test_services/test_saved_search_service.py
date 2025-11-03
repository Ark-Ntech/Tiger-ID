"""Tests for SavedSearchService"""

import pytest
from uuid import uuid4

from backend.services.saved_search_service import SavedSearchService
from backend.database.models import SavedSearch


class TestSavedSearchService:
    """Tests for SavedSearchService"""
    
    def test_create_saved_search(self, db_session, sample_user_id):
        """Test creating a saved search"""
        service = SavedSearchService(db_session)
        
        search = service.create_saved_search(
            user_id=sample_user_id,
            name="Test Search",
            search_criteria={"query": "tiger facility", "type": "investigation"},
            alert_enabled=False
        )
        
        assert search.user_id == sample_user_id
        assert search.name == "Test Search"
        assert search.search_criteria == {"query": "tiger facility", "type": "investigation"}
        assert search.alert_enabled is False
    
    def test_get_saved_search(self, db_session, sample_user_id):
        """Test getting saved search by ID"""
        service = SavedSearchService(db_session)
        
        created = service.create_saved_search(
            user_id=sample_user_id,
            name="Test Search",
            search_criteria={"query": "test"},
            alert_enabled=False
        )
        
        retrieved = service.get_saved_search(created.search_id)
        
        assert retrieved is not None
        assert retrieved.search_id == created.search_id
        assert retrieved.name == "Test Search"
    
    def test_get_saved_searches(self, db_session, sample_user_id):
        """Test getting saved searches"""
        service = SavedSearchService(db_session)
        
        # Create multiple searches
        service.create_saved_search(
            user_id=sample_user_id,
            name="Search 1",
            search_criteria={"query": "test1"},
            alert_enabled=False
        )
        service.create_saved_search(
            user_id=sample_user_id,
            name="Search 2",
            search_criteria={"query": "test2"},
            alert_enabled=True
        )
        
        searches = service.get_saved_searches(user_id=sample_user_id)
        
        assert len(searches) >= 2
    
    def test_get_saved_searches_filter_alert_enabled(self, db_session, sample_user_id):
        """Test getting saved searches filtered by alert enabled"""
        service = SavedSearchService(db_session)
        
        # Create searches with different alert settings
        service.create_saved_search(
            user_id=sample_user_id,
            name="Alert Search",
            search_criteria={"query": "test"},
            alert_enabled=True
        )
        service.create_saved_search(
            user_id=sample_user_id,
            name="No Alert Search",
            search_criteria={"query": "test"},
            alert_enabled=False
        )
        
        alert_searches = service.get_saved_searches(
            user_id=sample_user_id,
            alert_enabled=True
        )
        
        assert len(alert_searches) >= 1
        assert all(s.alert_enabled is True for s in alert_searches)
    
    def test_update_saved_search(self, db_session, sample_user_id):
        """Test updating saved search"""
        service = SavedSearchService(db_session)
        
        search = service.create_saved_search(
            user_id=sample_user_id,
            name="Original Name",
            search_criteria={"query": "test"},
            alert_enabled=False
        )
        
        updated = service.update_saved_search(
            search.search_id,
            name="Updated Name",
            alert_enabled=True
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.alert_enabled is True
    
    def test_delete_saved_search(self, db_session, sample_user_id):
        """Test deleting saved search"""
        service = SavedSearchService(db_session)
        
        search = service.create_saved_search(
            user_id=sample_user_id,
            name="To Delete",
            search_criteria={"query": "test"},
            alert_enabled=False
        )
        
        search_id = search.search_id
        
        result = service.delete_saved_search(search_id)
        
        assert result is True
        
        # Verify deleted
        retrieved = service.get_saved_search(search_id)
        assert retrieved is None
    
    def test_execute_saved_search(self, db_session, sample_user_id):
        """Test executing saved search"""
        service = SavedSearchService(db_session)
        
        search = service.create_saved_search(
            user_id=sample_user_id,
            name="Test Search",
            search_criteria={"query": "tiger", "type": "investigation"},
            alert_enabled=False
        )
        
        results = service.execute_saved_search(search.search_id)
        
        assert "results" in results or "investigations" in results or isinstance(results, dict)

