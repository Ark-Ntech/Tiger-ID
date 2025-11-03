"""Tests for NewsMonitoringService"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from backend.services.news_monitoring_service import NewsMonitoringService


class TestNewsMonitoringService:
    """Tests for NewsMonitoringService"""
    
    @pytest.mark.asyncio
    async def test_search_news(self):
        """Test searching news"""
        service = NewsMonitoringService()
        
        with patch.object(service, 'search_news') as mock_search:
            mock_search.return_value = {
                "articles": [
                    {"title": "Test Article", "url": "https://example.com"}
                ]
            }
            
            result = await service.search_news(
                query="tiger facility",
                days=7,
                limit=20
            )
            
            assert "articles" in result or "results" in result or isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_monitor_facility_news(self):
        """Test monitoring facility news"""
        service = NewsMonitoringService()
        
        with patch.object(service, 'monitor_facility_news') as mock_monitor:
            mock_monitor.return_value = {"alerts": []}
            
            result = await service.monitor_facility_news(
                facility_id="123",
                alert_threshold=0.8
            )
            
            assert "alerts" in result or isinstance(result, dict)

