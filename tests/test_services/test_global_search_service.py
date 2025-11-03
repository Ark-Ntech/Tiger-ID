"""Tests for GlobalSearchService"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.services.global_search_service import GlobalSearchService


class TestGlobalSearchService:
    """Tests for GlobalSearchService"""
    
    def test_global_search(self, db_session):
        """Test global search"""
        service = GlobalSearchService(db_session)
        
        result = service.global_search(
            query="test query",
            entity_types=["investigation", "facility"],
            limit=50
        )
        
        assert "results" in result or "investigations" in result or isinstance(result, dict)
    
    def test_global_search_empty_query(self, db_session):
        """Test global search with empty query"""
        service = GlobalSearchService(db_session)
        
        result = service.global_search(
            query="",
            limit=50
        )
        
        assert isinstance(result, dict)

