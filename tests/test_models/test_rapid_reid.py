"""Tests for RAPID ReID model wrapper."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import io


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.models.rapid.path = "/models/rapid"
    settings.models.rapid.similarity_threshold = 0.8
    return settings


@pytest.fixture
def mock_modal_client():
    """Create mock Modal client."""
    client = MagicMock()
    client.rapid_reid_embedding = AsyncMock(return_value={
        "success": True,
        "embedding": [0.1] * 2048
    })
    return client


@pytest.fixture
def sample_image():
    """Create a sample PIL image."""
    return Image.new('RGB', (224, 224), color='white')


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes."""
    img = Image.new('RGB', (224, 224), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


class TestRAPIDReIDModel:
    """Tests for RAPIDReIDModel class."""

    def test_model_initialization(self, mock_settings, mock_modal_client):
        """Test model initialization."""
        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()

            assert model.embedding_dim == 2048
            assert model.similarity_threshold == 0.8

    def test_embedding_dimension(self, mock_settings, mock_modal_client):
        """Test embedding dimension."""
        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()

            assert model.embedding_dim == 2048

    @pytest.mark.asyncio
    async def test_load_model(self, mock_settings, mock_modal_client):
        """Test load_model is a no-op for Modal backend."""
        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()
            await model.load_model()  # Should not raise

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, mock_settings, mock_modal_client, sample_image):
        """Test successful embedding generation."""
        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()
            embedding = await model.generate_embedding(sample_image)

            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (2048,)
            # Verify normalized
            assert np.isclose(np.linalg.norm(embedding), 1.0, atol=0.01)

    @pytest.mark.asyncio
    async def test_generate_embedding_from_bytes(self, mock_settings, mock_modal_client, sample_image_bytes):
        """Test embedding generation from bytes."""
        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()
            embedding = await model.generate_embedding(sample_image_bytes)

            assert isinstance(embedding, np.ndarray)

    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, mock_settings, mock_modal_client, sample_image):
        """Test embedding generation failure."""
        mock_modal_client.rapid_reid_embedding.return_value = {
            "success": False,
            "error": "Model inference failed"
        }

        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()

            with pytest.raises(RuntimeError, match="Modal embedding generation failed"):
                await model.generate_embedding(sample_image)

    @pytest.mark.asyncio
    async def test_generate_embedding_queued(self, mock_settings, mock_modal_client, sample_image):
        """Test handling of queued requests."""
        mock_modal_client.rapid_reid_embedding.return_value = {
            "success": False,
            "queued": True,
            "error": "Request queued"
        }

        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()

            with pytest.raises(RuntimeError, match="queued"):
                await model.generate_embedding(sample_image)

    def test_compare_embeddings_identical(self, mock_settings, mock_modal_client):
        """Test comparison of identical embeddings."""
        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()
            embedding = np.array([1.0, 0.0, 0.0])
            similarity = model.compare_embeddings(embedding, embedding)

            assert np.isclose(similarity, 1.0)

    def test_compare_embeddings_orthogonal(self, mock_settings, mock_modal_client):
        """Test comparison of orthogonal embeddings."""
        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            from backend.models.rapid_reid import RAPIDReIDModel

            model = RAPIDReIDModel()
            embedding1 = np.array([1.0, 0.0, 0.0])
            embedding2 = np.array([0.0, 1.0, 0.0])
            similarity = model.compare_embeddings(embedding1, embedding2)

            assert np.isclose(similarity, 0.0)
