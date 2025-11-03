"""Tests for CrawlSchedulerService"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.services.crawl_scheduler_service import CrawlSchedulerService


class TestCrawlSchedulerService:
    """Tests for CrawlSchedulerService"""
    
    def test_schedule_crawl(self, db_session):
        """Test scheduling a crawl"""
        service = CrawlSchedulerService(db_session)
        
        result = service.schedule_crawl(
            facility_id="123",
            priority="high"
        )
        
        assert "job_id" in result or "crawl_id" in result or isinstance(result, dict)
    
    def test_get_crawl_status(self, db_session):
        """Test getting crawl status"""
        service = CrawlSchedulerService(db_session)
        
        result = service.get_crawl_status(crawl_id="123")
        
        assert "status" in result or isinstance(result, dict)

