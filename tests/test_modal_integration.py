"""Tests for Modal integration and model inference"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import numpy as np
import io

from backend.services.modal_client import ModalClient, ModalUnavailableError, ModalClientError
from backend.models.reid import TigerReIDModel
from backend.models.detection import TigerDetectionModel
from backend.models.rapid_reid import RAPIDReIDModel
from backend.models.wildlife_tools import WildlifeToolsReIDModel
from backend.models.cvwc2019_reid import CVWC2019ReIDModel


# Test fixtures

@pytest.fixture
def sample_image():
    """Create a sample test image"""
    img = Image.new('RGB', (256, 256), color='red')
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes"""
    buffer = io.BytesIO()
    sample_image.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def mock_modal_client():
    """Create a mock Modal client"""
    client = Mock(spec=ModalClient)
    
    # Mock successful responses
    client.tiger_reid_embedding = AsyncMock(return_value={
        "success": True,
        "embedding": np.random.rand(2048).tolist(),
        "shape": (2048,)
    })
    
    client.megadetector_detect = AsyncMock(return_value={
        "success": True,
        "detections": [
            {
                "bbox": [10.0, 10.0, 100.0, 100.0],
                "confidence": 0.95,
                "category": "animal",
                "class_id": 0
            }
        ],
        "num_detections": 1
    })
    
    client.rapid_reid_embedding = AsyncMock(return_value={
        "success": True,
        "embedding": np.random.rand(2048).tolist(),
        "shape": (2048,)
    })
    
    client.wildlife_tools_embedding = AsyncMock(return_value={
        "success": True,
        "embedding": np.random.rand(1536).tolist(),
        "shape": (1536,)
    })
    
    client.cvwc2019_reid_embedding = AsyncMock(return_value={
        "success": True,
        "embedding": np.random.rand(2048).tolist(),
        "shape": (2048,)
    })
    
    client.omnivinci_analyze_video = AsyncMock(return_value={
        "success": True,
        "analysis": {
            "description": "Test video analysis result",
            "detected_objects": ["tiger"],
            "confidence": 0.95
        }
    })
    
    return client


# ModalClient Tests

class TestModalClient:
    """Tests for ModalClient"""
    
    @pytest.mark.asyncio
    async def test_modal_client_initialization(self):
        """Test Modal client initialization"""
        client = ModalClient(
            max_retries=3,
            retry_delay=1.0,
            timeout=120,
            queue_max_size=100
        )

        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        # Timeout is capped at DEFAULT_SINGLE_TIMEOUT (60)
        assert client.timeout == 60
        assert client.queue_max_size == 100
        assert client.stats["requests_sent"] == 0
        assert client.stats["requests_succeeded"] == 0
        assert client.stats["requests_failed"] == 0
    
    @pytest.mark.asyncio
    async def test_tiger_reid_embedding_success(self, mock_modal_client, sample_image):
        """Test successful tiger ReID embedding"""
        result = await mock_modal_client.tiger_reid_embedding(sample_image)
        
        assert result["success"] is True
        assert "embedding" in result
        assert len(result["embedding"]) > 0
    
    @pytest.mark.asyncio
    async def test_megadetector_detect_success(self, mock_modal_client, sample_image):
        """Test successful MegaDetector detection"""
        result = await mock_modal_client.megadetector_detect(
            sample_image,
            confidence_threshold=0.5
        )
        
        assert result["success"] is True
        assert "detections" in result
        assert len(result["detections"]) > 0
        assert result["detections"][0]["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_modal_unavailable_with_fallback(self, sample_image):
        """Test fallback to mock when Modal unavailable"""
        client = ModalClient()

        # Mock Modal to be unavailable
        with patch.object(client, '_get_modal_function', side_effect=ModalUnavailableError("Modal unavailable")):
            result = await client.tiger_reid_embedding(
                sample_image,
                fallback_to_queue=True
            )

            # Should return mock embedding instead of raising
            assert result.get("success") is True
            assert "embedding" in result
            assert result.get("mock") is True

    @pytest.mark.asyncio
    async def test_modal_unavailable_fallback_also_works_without_queue_flag(self, sample_image):
        """Test that fallback occurs even when fallback_to_queue=False"""
        client = ModalClient()

        # Mock Modal to be unavailable
        with patch.object(client, '_get_modal_function', side_effect=ModalUnavailableError("Modal unavailable")):
            result = await client.tiger_reid_embedding(
                sample_image,
                fallback_to_queue=False
            )

            # Current implementation still returns mock, doesn't raise
            assert result.get("success") is True
            assert "embedding" in result
            assert result.get("mock") is True
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, sample_image):
        """Test retry logic on failures"""
        client = ModalClient(max_retries=3, retry_delay=0.1)
        
        # Mock function that fails twice then succeeds
        call_count = 0
        async def mock_remote(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return {
                "success": True,
                "embedding": np.random.rand(2048).tolist()
            }
        
        with patch.object(client, '_get_modal_function') as mock_get:
            mock_func = Mock()
            mock_func.remote.aio = mock_remote
            mock_get.return_value = mock_func
            
            result = await client._call_with_retry(mock_func)
            
            assert result["success"] is True
            assert call_count == 3  # Failed twice, succeeded on third


# TigerReIDModel Tests

class TestTigerReIDModel:
    """Tests for TigerReIDModel with Modal backend"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, sample_image):
        """Test generating embedding via Modal"""
        model = TigerReIDModel()
        
        with patch.object(model.modal_client, 'tiger_reid_embedding', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "success": True,
                "embedding": np.random.rand(2048).tolist()
            }
            
            embedding = await model.generate_embedding(sample_image)
            
            assert embedding is not None
            assert isinstance(embedding, np.ndarray)
            assert len(embedding) > 0
            # Check normalization
            assert np.isclose(np.linalg.norm(embedding), 1.0)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, sample_image):
        """Test handling of embedding generation failure"""
        model = TigerReIDModel()
        
        with patch.object(model.modal_client, 'tiger_reid_embedding', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "success": False,
                "error": "Model inference failed"
            }
            
            with pytest.raises(RuntimeError):
                await model.generate_embedding(sample_image)
    
    def test_compute_similarity(self):
        """Test computing similarity between embeddings"""
        model = TigerReIDModel()
        
        # Create two similar embeddings
        embedding1 = np.random.rand(2048)
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        
        embedding2 = embedding1 + np.random.rand(2048) * 0.1
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        similarity = model.compute_similarity(embedding1, embedding2)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.8  # Should be high for similar embeddings


# TigerDetectionModel Tests

class TestTigerDetectionModel:
    """Tests for TigerDetectionModel with Modal backend"""
    
    @pytest.mark.asyncio
    async def test_detect(self, sample_image_bytes, sample_image):
        """Test detecting tigers via Modal"""
        model = TigerDetectionModel()
        
        with patch.object(model.modal_client, 'megadetector_detect', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "success": True,
                "detections": [
                    {
                        "bbox": [10.0, 10.0, 100.0, 100.0],
                        "confidence": 0.95,
                        "category": "animal",
                        "class_id": 0
                    }
                ],
                "num_detections": 1
            }
            
            result = await model.detect(sample_image_bytes)
            
            assert result["count"] > 0
            assert len(result["detections"]) > 0
            
            detection = result["detections"][0]
            assert "bbox" in detection
            assert "confidence" in detection
            assert detection["confidence"] > 0.5
            assert "crop" in detection
            assert isinstance(detection["crop"], Image.Image)
    
    @pytest.mark.asyncio
    async def test_detect_no_animals(self, sample_image_bytes):
        """Test detection with no animals found"""
        model = TigerDetectionModel()
        
        with patch.object(model.modal_client, 'megadetector_detect', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "success": True,
                "detections": [],
                "num_detections": 0
            }
            
            result = await model.detect(sample_image_bytes)
            
            assert result["count"] == 0
            assert len(result["detections"]) == 0


# RAPIDReIDModel Tests

class TestRAPIDReIDModel:
    """Tests for RAPIDReIDModel with Modal backend"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, sample_image_bytes):
        """Test generating RAPID embedding via Modal"""
        model = RAPIDReIDModel()
        
        with patch.object(model.modal_client, 'rapid_reid_embedding', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "success": True,
                "embedding": np.random.rand(2048).tolist()
            }
            
            embedding = await model.generate_embedding(sample_image_bytes)
            
            assert embedding is not None
            assert isinstance(embedding, np.ndarray)
            assert np.isclose(np.linalg.norm(embedding), 1.0)
    
    def test_compare_embeddings(self):
        """Test comparing RAPID embeddings"""
        model = RAPIDReIDModel()
        
        embedding1 = np.random.rand(2048)
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        
        embedding2 = np.random.rand(2048)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        similarity = model.compare_embeddings(embedding1, embedding2)
        
        assert 0.0 <= similarity <= 1.0


# WildlifeToolsReIDModel Tests

class TestWildlifeToolsReIDModel:
    """Tests for WildlifeToolsReIDModel with Modal backend"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, sample_image_bytes):
        """Test generating WildlifeTools embedding via Modal"""
        model = WildlifeToolsReIDModel()
        
        with patch.object(model.modal_client, 'wildlife_tools_embedding', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "success": True,
                "embedding": np.random.rand(1536).tolist()
            }
            
            embedding = await model.generate_embedding(sample_image_bytes)
            
            assert embedding is not None
            assert isinstance(embedding, np.ndarray)
            assert np.isclose(np.linalg.norm(embedding), 1.0)
    
    def test_identify(self):
        """Test k-NN identification"""
        model = WildlifeToolsReIDModel()
        
        # Create query and database embeddings
        query_embedding = np.random.rand(1536)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        db_embeddings = [
            np.random.rand(1536) / np.linalg.norm(np.random.rand(1536))
            for _ in range(5)
        ]
        db_labels = ["tiger1", "tiger2", "tiger3", "tiger4", "tiger5"]
        
        # Make first database embedding very similar to query
        db_embeddings[0] = query_embedding + np.random.rand(1536) * 0.01
        db_embeddings[0] = db_embeddings[0] / np.linalg.norm(db_embeddings[0])
        
        predicted_label, similarity = model.identify(
            query_embedding,
            db_embeddings,
            db_labels,
            k=1
        )
        
        assert predicted_label == "tiger1"
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.9  # Should be high for similar embedding


# CVWC2019ReIDModel Tests

class TestCVWC2019ReIDModel:
    """Tests for CVWC2019ReIDModel with Modal backend"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, sample_image_bytes):
        """Test generating CVWC2019 embedding via Modal"""
        model = CVWC2019ReIDModel()
        
        with patch.object(model.modal_client, 'cvwc2019_reid_embedding', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "success": True,
                "embedding": np.random.rand(2048).tolist()
            }
            
            embedding = await model.generate_embedding(sample_image_bytes)
            
            assert embedding is not None
            assert isinstance(embedding, np.ndarray)
            assert np.isclose(np.linalg.norm(embedding), 1.0)
    
    def test_compare_embeddings(self):
        """Test comparing CVWC2019 embeddings"""
        model = CVWC2019ReIDModel()
        
        embedding1 = np.random.rand(2048)
        embedding2 = np.random.rand(2048)
        
        similarity = model.compare_embeddings(embedding1, embedding2)
        
        assert 0.0 <= similarity <= 1.0


# Integration Tests

class TestModalIntegration:
    """Integration tests for Modal system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_tiger_identification(self, sample_image):
        """Test end-to-end tiger identification workflow"""
        # Initialize models
        detection_model = TigerDetectionModel()
        reid_model = TigerReIDModel()
        
        # Mock Modal responses
        with patch.object(detection_model.modal_client, 'megadetector_detect', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {
                "success": True,
                "detections": [
                    {
                        "bbox": [10.0, 10.0, 100.0, 100.0],
                        "confidence": 0.95,
                        "category": "animal",
                        "class_id": 0
                    }
                ]
            }
            
            with patch.object(reid_model.modal_client, 'tiger_reid_embedding', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = {
                    "success": True,
                    "embedding": np.random.rand(2048).tolist()
                }
                
                # Convert image to bytes
                buffer = io.BytesIO()
                sample_image.save(buffer, format='JPEG')
                image_bytes = buffer.getvalue()
                
                # Step 1: Detect tigers
                detections = await detection_model.detect(image_bytes)
                assert detections["count"] > 0
                
                # Step 2: Generate embeddings for each detection
                for detection in detections["detections"]:
                    crop = detection["crop"]
                    embedding = await reid_model.generate_embedding(crop)
                    
                    assert embedding is not None
                    assert len(embedding) > 0
    
    @pytest.mark.asyncio
    async def test_modal_statistics(self):
        """Test Modal client statistics tracking"""
        client = ModalClient()
        
        initial_stats = client.get_stats()
        assert initial_stats["requests_sent"] == 0
        assert initial_stats["queue_size"] == 0
        
        # Stats are updated during actual operations
        # Here we just verify the structure
        assert "requests_succeeded" in initial_stats
        assert "requests_failed" in initial_stats
        assert "queue_max_size" in initial_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

