"""Tests for search routes"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# python-jose is now properly installed in requirements.txt

from backend.api.app import create_app
from backend.database.models import User


class TestSearchRoutes:
    """Tests for search API routes"""
    
    def test_global_search(self, test_client, auth_headers):
        """Test global search endpoint"""
        response = test_client.get(
            "/api/v1/search/global?q=test&limit=50",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or isinstance(data, dict)
    
    def test_global_search_with_entity_types(self, test_client, auth_headers):
        """Test global search with entity type filter"""
        response = test_client.get(
            "/api/v1/search/global?q=test&entity_types=investigation,facility&limit=50",
            headers=auth_headers
        )
        
        assert response.status_code == 200

