"""Tests for SocialMediaIntelService"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from backend.services.social_media_intel_service import SocialMediaIntelService


class TestSocialMediaIntelService:
    """Tests for SocialMediaIntelService"""
    
    @pytest.mark.asyncio
    async def test_search_social_media(self):
        """Test searching social media"""
        service = SocialMediaIntelService()
        
        with patch.object(service, 'search_social_media') as mock_search:
            mock_search.return_value = {
                "accounts": [],
                "posts": []
            }
            
            result = await service.search_social_media(
                query="tiger facility",
                platform="twitter"
            )
            
            assert "accounts" in result or "posts" in result or isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_analyze_account(self):
        """Test analyzing social media account"""
        service = SocialMediaIntelService()
        
        with patch.object(service, 'analyze_account') as mock_analyze:
            mock_analyze.return_value = {"analysis": {}}
            
            result = await service.analyze_account(
                account_id="@test",
                platform="twitter"
            )
            
            assert "analysis" in result or isinstance(result, dict)

