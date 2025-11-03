"""Tests for EmbeddingService"""

import pytest
import numpy as np
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from backend.services.embedding_service import EmbeddingService
from backend.database.models import TigerImage


class TestEmbeddingService:
    """Tests for EmbeddingService"""
    
    def test_store_image_embedding(self, db_session):
        """Test storing image embedding"""
        service = EmbeddingService(db_session)
        
        image_id = uuid4()
        embedding = np.random.rand(512).astype(np.float32)
        
        with patch('backend.services.embedding_service.store_embedding') as mock_store:
            mock_store.return_value = True
            result = service.store_image_embedding(image_id, embedding)
            
            assert result is True
            mock_store.assert_called_once()
    
    def test_find_matching_tigers_by_embedding(self, db_session):
        """Test finding matching tigers by embedding"""
        service = EmbeddingService(db_session)
        
        query_embedding = np.random.rand(512).astype(np.float32)
        tiger_id = uuid4()
        
        with patch('backend.services.embedding_service.find_matching_tigers') as mock_find:
            mock_find.return_value = [
                {
                    "tiger_id": str(tiger_id),
                    "similarity": 0.95,
                    "image_path": "/path/to/image.jpg"
                }
            ]
            
            result = service.find_matching_tigers_by_embedding(
                query_embedding,
                tiger_id=tiger_id,
                limit=5,
                similarity_threshold=0.8
            )
            
            assert len(result) == 1
            assert result[0]["similarity"] == 0.95
    
    def test_search_similar_images(self, db_session):
        """Test searching for similar images"""
        service = EmbeddingService(db_session)
        
        query_embedding = np.random.rand(512).astype(np.float32)
        
        with patch('backend.services.embedding_service.search_similar_embeddings') as mock_search:
            mock_search.return_value = [
                ("image_id_1", 0.95),
                ("image_id_2", 0.90)
            ]
            
            result = service.search_similar_images(
                query_embedding,
                limit=10,
                similarity_threshold=0.8
            )
            
            assert len(result) == 2
            assert result[0][1] == 0.95
    
    def test_get_image_embedding(self, db_session):
        """Test getting image embedding"""
        service = EmbeddingService(db_session)
        
        image_id = uuid4()
        embedding = np.random.rand(512).astype(np.float32)
        
        # Create mock image with embedding
        mock_image = MagicMock()
        mock_image.embedding = embedding.tolist()
        
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_image
            
            result = service.get_image_embedding(image_id)
            
            assert result is not None
            assert isinstance(result, np.ndarray)
    
    def test_get_image_embedding_not_found(self, db_session):
        """Test getting embedding for nonexistent image"""
        service = EmbeddingService(db_session)
        
        image_id = uuid4()
        
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            result = service.get_image_embedding(image_id)
            
            assert result is None
    
    def test_update_image_embedding(self, db_session):
        """Test updating image embedding"""
        service = EmbeddingService(db_session)
        
        image_id = uuid4()
        embedding = np.random.rand(512).astype(np.float32)
        
        mock_image = MagicMock()
        mock_image.image_id = image_id
        
        with patch.object(db_session, 'query') as mock_query, \
             patch('backend.services.embedding_service.store_embedding') as mock_store:
            mock_query.return_value.filter.return_value.first.return_value = mock_image
            mock_store.return_value = True
            
            result = service.update_image_embedding(image_id, embedding, side_view="left")
            
            assert result is True
            mock_store.assert_called_once()
            assert mock_image.side_view == "left"
    
    def test_update_image_embedding_not_found(self, db_session):
        """Test updating embedding for nonexistent image"""
        service = EmbeddingService(db_session)
        
        image_id = uuid4()
        embedding = np.random.rand(512).astype(np.float32)
        
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            result = service.update_image_embedding(image_id, embedding)
            
            assert result is False

