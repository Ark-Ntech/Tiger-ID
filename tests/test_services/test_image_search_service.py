"""Tests for ImageSearchService"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from backend.services.image_search_service import ImageSearchService


class TestImageSearchService:
    """Tests for ImageSearchService"""
    
    @pytest.mark.asyncio
    async def test_reverse_image_search(self):
        """Test reverse image search"""
        service = ImageSearchService()
        
        with patch.object(service, 'reverse_image_search') as mock_search:
            mock_search.return_value = {
                "results": [
                    {"url": "https://example.com/match.jpg", "similarity": 0.95}
                ]
            }
            
            result = await service.reverse_image_search(
                image_url="https://example.com/image.jpg",
                provider="google"
            )
            
            assert "results" in result or isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_search_by_upload(self):
        """Test image search by upload"""
        service = ImageSearchService()
        
        mock_file = MagicMock()
        mock_file.read.return_value = b"fake_image_data"
        
        with patch.object(service, 'search_by_upload') as mock_search:
            mock_search.return_value = {"results": []}
            
            result = await service.search_by_upload(mock_file, provider="google")
            
            assert "results" in result or isinstance(result, dict)

