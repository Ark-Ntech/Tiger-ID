"""Tests for LeadGenerationService"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from backend.services.lead_generation_service import LeadGenerationService


class TestLeadGenerationService:
    """Tests for LeadGenerationService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance"""
        return LeadGenerationService()
    
    @pytest.mark.asyncio
    @patch('backend.services.lead_generation_service.get_web_search_service')
    async def test_search_suspicious_listings(self, mock_get_search):
        """Test searching for suspicious listings"""
        service = LeadGenerationService()
        
        # Mock web search service
        mock_search_service = AsyncMock()
        mock_search_service.search.return_value = {
            "results": [
                {
                    "title": "Tiger for Sale",
                    "url": "https://example.com/sale",
                    "snippet": "Beautiful tiger cub for sale"
                }
            ]
        }
        mock_get_search.return_value = mock_search_service
        service.web_search = mock_search_service
        
        result = await service.search_suspicious_listings(location="California", limit=20)
        
        assert "listings" in result
        assert "count" in result
        assert isinstance(result["listings"], list)
    
    @pytest.mark.asyncio
    @patch('backend.services.lead_generation_service.get_web_search_service')
    async def test_search_suspicious_listings_no_location(self, mock_get_search):
        """Test searching for suspicious listings without location"""
        service = LeadGenerationService()
        
        mock_search_service = AsyncMock()
        mock_search_service.search.return_value = {"results": []}
        mock_get_search.return_value = mock_search_service
        service.web_search = mock_search_service
        
        result = await service.search_suspicious_listings(limit=20)
        
        assert "listings" in result
        assert isinstance(result["listings"], list)
    
    def test_score_listing_suspiciousness(self):
        """Test scoring listing suspiciousness"""
        service = LeadGenerationService()
        
        # High suspiciousness listing
        listing = {
            "title": "Tiger cub for sale cheap",
            "snippet": "No papers needed, cash only"
        }
        score = service._score_listing_suspiciousness(listing)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    def test_deduplicate_listings(self):
        """Test deduplicating listings"""
        service = LeadGenerationService()
        
        listings = [
            {"url": "https://example.com/1", "title": "Listing 1"},
            {"url": "https://example.com/1", "title": "Listing 1"},  # Duplicate
            {"url": "https://example.com/2", "title": "Listing 2"}
        ]
        
        deduplicated = service._deduplicate_listings(listings)
        
        assert len(deduplicated) == 2
        assert deduplicated[0]["url"] != deduplicated[1]["url"]
    
    @pytest.mark.asyncio
    @patch('backend.services.lead_generation_service.get_web_search_service')
    async def test_search_social_media_leads(self, mock_get_search):
        """Test searching for social media leads"""
        service = LeadGenerationService()
        
        mock_search_service = AsyncMock()
        mock_search_service.search.return_value = {"results": []}
        mock_get_search.return_value = mock_search_service
        service.web_search = mock_search_service
        
        result = await service.search_social_media_leads(location="California")
        
        assert "accounts" in result or "results" in result
    
    @pytest.mark.asyncio
    @patch('backend.services.lead_generation_service.get_web_search_service')
    async def test_generate_leads(self, mock_get_search):
        """Test generating leads"""
        service = LeadGenerationService()
        
        mock_search_service = AsyncMock()
        mock_search_service.search.return_value = {"results": []}
        mock_get_search.return_value = mock_search_service
        service.web_search = mock_search_service
        
        result = await service.generate_leads(
            location="California",
            include_listings=True,
            include_social_media=True
        )
        
        assert "listings" in result or "social_media" in result or "leads" in result

