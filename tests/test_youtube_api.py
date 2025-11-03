"""Tests for YouTube API client"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.services.external_apis.youtube_client import YouTubeClient


class TestYouTubeClient:
    """Tests for YouTubeClient"""
    
    @pytest.fixture
    def youtube_client(self):
        """Create YouTube client instance"""
        return YouTubeClient(api_key="test_api_key")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, youtube_client):
        """Test successful health check"""
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"items": []}
            
            result = await youtube_client.health_check()
            
            assert result is True
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, youtube_client):
        """Test health check failure"""
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("API error")
            
            result = await youtube_client.health_check()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_search_videos(self, youtube_client):
        """Test video search"""
        mock_response = {
            "items": [
                {
                    "id": {"videoId": "test_video_id"},
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test description",
                        "channelId": "test_channel",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "thumbnails": {"default": {"url": "http://thumbnail.url"}}
                    }
                }
            ]
        }
        
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            with patch.object(youtube_client, 'get_video_details', new_callable=AsyncMock) as mock_details:
                mock_request.return_value = mock_response
                mock_details.return_value = {
                    "video_id": "test_video_id",
                    "view_count": 1000,
                    "like_count": 50,
                    "comment_count": 10,
                    "duration": "PT5M30S",
                    "tags": ["tag1"]
                }
                
                videos = await youtube_client.search_videos("test query", max_results=1)
                
                assert len(videos) == 1
                assert videos[0]["video_id"] == "test_video_id"
                assert videos[0]["title"] == "Test Video"
                assert videos[0]["statistics"]["viewCount"] == 1000
                assert videos[0]["duration"] == "PT5M30S"
                assert videos[0]["tags"] == ["tag1"]
                mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_videos_with_none_video_details(self, youtube_client):
        """Test video search when get_video_details returns None"""
        mock_response = {
            "items": [
                {
                    "id": {"videoId": "test_video_id"},
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test description",
                        "channelId": "test_channel",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "thumbnails": {"default": {"url": "http://thumbnail.url"}}
                    }
                }
            ]
        }
        
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            with patch.object(youtube_client, 'get_video_details', new_callable=AsyncMock) as mock_details:
                mock_request.return_value = mock_response
                mock_details.return_value = None
                
                videos = await youtube_client.search_videos("test query", max_results=1)
                
                assert len(videos) == 1
                assert videos[0]["video_id"] == "test_video_id"
                assert videos[0]["title"] == "Test Video"
                assert videos[0]["statistics"] == {}
                assert videos[0]["duration"] == ""
                assert videos[0]["tags"] == []
                mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_channel_info(self, youtube_client):
        """Test get channel info"""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Channel",
                        "description": "Channel description",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "thumbnails": {"default": {"url": "http://thumbnail.url"}},
                        "country": "US"
                    },
                    "statistics": {
                        "viewCount": "1000000",
                        "subscriberCount": "10000",
                        "videoCount": "100"
                    },
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "playlist_id"}
                    }
                }
            ]
        }
        
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            channel_info = await youtube_client.get_channel_info("test_channel_id")
            
            assert channel_info is not None
            assert channel_info["channel_id"] == "test_channel_id"
            assert channel_info["title"] == "Test Channel"
            assert channel_info["view_count"] == 1000000
    
    @pytest.mark.asyncio
    async def test_get_channel_info_not_found(self, youtube_client):
        """Test get channel info when channel not found"""
        mock_response = {"items": []}
        
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            channel_info = await youtube_client.get_channel_info("nonexistent_channel")
            
            assert channel_info is None
    
    @pytest.mark.asyncio
    async def test_get_video_details(self, youtube_client):
        """Test get video details"""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Video",
                        "description": "Description",
                        "channelId": "channel_id",
                        "channelTitle": "Channel",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "tags": ["tag1", "tag2"],
                        "categoryId": "22",
                        "thumbnails": {"high": {"url": "http://thumbnail.url"}}
                    },
                    "statistics": {
                        "viewCount": "5000",
                        "likeCount": "100",
                        "commentCount": "50"
                    },
                    "contentDetails": {
                        "duration": "PT5M30S"
                    }
                }
            ]
        }
        
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            video_details = await youtube_client.get_video_details("test_video_id")
            
            assert video_details is not None
            assert video_details["video_id"] == "test_video_id"
            assert video_details["title"] == "Test Video"
            assert video_details["view_count"] == 5000
    
    @pytest.mark.asyncio
    async def test_get_video_comments(self, youtube_client):
        """Test get video comments"""
        mock_response = {
            "items": [
                {
                    "id": "comment_id",
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "Test User",
                                "textDisplay": "Great video!",
                                "publishedAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z",
                                "likeCount": 10
                            }
                        },
                        "totalReplyCount": 2
                    }
                }
            ]
        }
        
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            comments = await youtube_client.get_video_comments("test_video_id", max_results=10)
            
            assert len(comments) == 1
            assert comments[0]["author"] == "Test User"
            assert comments[0]["text"] == "Great video!"
    
    @pytest.mark.asyncio
    async def test_get_channel_videos(self, youtube_client):
        """Test get channel videos"""
        channel_info_response = {
            "channel_id": "test_channel",
            "upload_playlist_id": "playlist_123"
        }
        playlist_response = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "test_video_id"},
                        "title": "Test Video",
                        "description": "Test description",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "thumbnails": {"default": {"url": "http://thumbnail.url"}}
                    }
                }
            ]
        }
        
        with patch.object(youtube_client, 'get_channel_info', new_callable=AsyncMock) as mock_channel_info:
            with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
                with patch.object(youtube_client, 'get_video_details', new_callable=AsyncMock) as mock_details:
                    mock_channel_info.return_value = channel_info_response
                    mock_request.return_value = playlist_response
                    mock_details.return_value = {
                        "video_id": "test_video_id",
                        "view_count": 1000,
                        "like_count": 50,
                        "comment_count": 10,
                        "duration": "PT5M30S"
                    }
                    
                    videos = await youtube_client.get_channel_videos("test_channel", max_results=1)
                    
                    assert len(videos) == 1
                    assert videos[0]["video_id"] == "test_video_id"
                    assert videos[0]["title"] == "Test Video"
                    assert videos[0]["statistics"]["viewCount"] == 1000
                    assert videos[0]["duration"] == "PT5M30S"
    
    @pytest.mark.asyncio
    async def test_get_channel_videos_with_none_video_details(self, youtube_client):
        """Test get channel videos when get_video_details returns None"""
        channel_info_response = {
            "channel_id": "test_channel",
            "upload_playlist_id": "playlist_123"
        }
        playlist_response = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "test_video_id"},
                        "title": "Test Video",
                        "description": "Test description",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "thumbnails": {"default": {"url": "http://thumbnail.url"}}
                    }
                }
            ]
        }
        
        with patch.object(youtube_client, 'get_channel_info', new_callable=AsyncMock) as mock_channel_info:
            with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
                with patch.object(youtube_client, 'get_video_details', new_callable=AsyncMock) as mock_details:
                    mock_channel_info.return_value = channel_info_response
                    mock_request.return_value = playlist_response
                    mock_details.return_value = None
                    
                    videos = await youtube_client.get_channel_videos("test_channel", max_results=1)
                    
                    assert len(videos) == 1
                    assert videos[0]["video_id"] == "test_video_id"
                    assert videos[0]["title"] == "Test Video"
                    assert videos[0]["statistics"] == {}
                    assert videos[0]["duration"] == ""
    
    @pytest.mark.asyncio
    async def test_search_channels(self, youtube_client):
        """Test channel search"""
        mock_response = {
            "items": [
                {
                    "id": {"channelId": "channel_id_1"}
                }
            ]
        }
        
        with patch.object(youtube_client, '_request', new_callable=AsyncMock) as mock_request:
            with patch.object(youtube_client, 'get_channel_info', new_callable=AsyncMock) as mock_info:
                mock_request.return_value = mock_response
                mock_info.return_value = {
                    "channel_id": "channel_id_1",
                    "title": "Test Channel",
                    "subscriber_count": 1000
                }
                
                channels = await youtube_client.search_channels("test query", max_results=1)
                
                assert len(channels) == 1
                assert channels[0]["channel_id"] == "channel_id_1"
    
    @pytest.mark.asyncio
    async def test_request_with_api_key(self, youtube_client):
        """Test that API key is added as query parameter"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {"items": []}
            mock_response.raise_for_status.return_value = None
            
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None
            mock_async_client.request = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            await youtube_client._request("GET", "/search", params={"q": "test"})
            
            # Verify key parameter was added
            call_args = mock_async_client.request.call_args
            assert call_args is not None
            # Check that params include the key
            assert "key" in (call_args[1] or {}).get("params", {})

