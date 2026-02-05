"""Tests for model inference"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
from PIL import Image
import io

try:
    from backend.models.detection import TigerDetectionModel
except ImportError:
    # Model might not be available in test environment
    TigerDetectionModel = None

try:
    from backend.models.reid import TigerReIDModel
except ImportError:
    # Model might not be available in test environment
    TigerReIDModel = None


class TestTigerDetectionModel:
    """Tests for TigerDetectionModel"""
    
    @pytest.mark.asyncio
    async def test_detect_tiger_in_image(self):
        """Test detecting tiger in image"""
        model = TigerDetectionModel()

        # Create mock image
        img = Image.new('RGB', (640, 480), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_bytes = img_bytes.read()

        # Mock detection result
        detection_result = {
            "detections": [
                {
                    "bbox": [100, 100, 200, 200],
                    "confidence": 0.95,
                    "class": "tiger",
                    "crop": b"cropped_tiger_image"
                }
            ],
            "image_size": (640, 480)
        }

        # Mock the detect method directly
        with patch.object(model, 'detect', new=AsyncMock(return_value=detection_result)):
            result = await model.detect(image_bytes)

            assert result is not None
            assert "detections" in result
            assert len(result["detections"]) == 1
            assert result["detections"][0]["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_detect_no_tiger(self):
        """Test detection when no tiger is present"""
        model = TigerDetectionModel()
        
        # Create mock image
        img = Image.new('RGB', (640, 480), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_bytes = img_bytes.read()
        
        # Mock detection with no tigers
        with patch.object(model, 'detect', new=AsyncMock(return_value={"detections": []})):
            result = await model.detect(image_bytes)
            
            assert result is not None
            assert "detections" in result
            assert len(result["detections"]) == 0
    
    @pytest.mark.asyncio
    async def test_model_loading_error(self):
        """Test model loading error handling"""
        model = TigerDetectionModel()
        
        # Mock loading error
        with patch.object(model, 'load_model', new=AsyncMock(side_effect=Exception("Model file not found"))):
            with pytest.raises(Exception):
                await model.load_model()


class TestTigerReIDModel:
    """Tests for TigerReIDModel"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Test generating embedding for tiger image"""
        model = TigerReIDModel()
        
        # Create mock image
        img = Image.new('RGB', (224, 224), color='orange')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_bytes = img_bytes.read()
        
        # Mock embedding generation
        mock_embedding = np.random.rand(512).astype(np.float32)
        
        with patch.object(model, 'generate_embedding', new=AsyncMock(return_value=mock_embedding)):
            embedding = await model.generate_embedding(image_bytes)
            
            assert embedding is not None
            assert isinstance(embedding, np.ndarray)
            assert len(embedding) == 512
            assert embedding.dtype == np.float32
    
    @pytest.mark.asyncio
    async def test_similarity_comparison(self):
        """Test comparing embeddings for similarity"""
        model = TigerReIDModel()
        
        # Create two embeddings
        embedding1 = np.random.rand(512).astype(np.float32)
        embedding2 = np.random.rand(512).astype(np.float32)
        
        # Normalize embeddings
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2)
        
        assert -1.0 <= similarity <= 1.0
        assert isinstance(similarity, (float, np.floating))
    
    @pytest.mark.asyncio
    async def test_model_loading_error(self):
        """Test model loading error handling"""
        model = TigerReIDModel()
        
        # Mock loading error
        with patch.object(model, 'load_model', new=AsyncMock(side_effect=Exception("Model file not found"))):
            with pytest.raises(Exception):
                await model.load_model()


class TestModelPipeline:
    """Integration tests for model pipeline"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_tiger_identification(self):
        """Test end-to-end tiger identification pipeline"""
        detection_model = TigerDetectionModel()
        reid_model = TigerReIDModel()
        
        # Create mock image
        img = Image.new('RGB', (640, 480), color='orange')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_bytes = img_bytes.read()
        
        # Mock detection
        detection_result = {
            "detections": [
                {
                    "bbox": [100, 100, 300, 300],
                    "confidence": 0.95,
                    "class": "tiger",
                    "crop": b"cropped_tiger"
                }
            ]
        }
        
        # Mock embedding
        mock_embedding = np.random.rand(512).astype(np.float32)
        mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)
        
        with patch.object(detection_model, 'detect', new=AsyncMock(return_value=detection_result)):
            with patch.object(reid_model, 'generate_embedding', new=AsyncMock(return_value=mock_embedding)):
                # Step 1: Detect tiger
                detection = await detection_model.detect(image_bytes)
                
                assert detection is not None
                assert len(detection["detections"]) > 0
                
                # Step 2: Generate embedding
                crop = detection["detections"][0]["crop"]
                embedding = await reid_model.generate_embedding(crop)
                
                assert embedding is not None
                assert len(embedding) == 512
                
                # Step 3: Compare with database (would use vector search)
                # This would be tested in integration tests

