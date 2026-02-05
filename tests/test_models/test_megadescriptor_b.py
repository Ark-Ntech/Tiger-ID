"""Tests for MegaDescriptor-B ReID model wrapper."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import io


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.models.megadescriptor_b.path = "/models/megadescriptor_b"
    settings.models.megadescriptor_b.similarity_threshold = 0.75
    return settings


@pytest.fixture
def mock_modal_client():
    """Create mock Modal client."""
    client = MagicMock()
    client.megadescriptor_b_embedding = AsyncMock(return_value={
        "success": True,
        "embedding": [0.1] * 1024
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


class TestMegaDescriptorBReIDModel:
    """Tests for MegaDescriptorBReIDModel class."""

    def test_model_initialization(self, mock_settings, mock_modal_client):
        """Test model initialization."""
        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()

            assert model.embedding_dim == 1024
            assert model.similarity_threshold == 0.75

    def test_embedding_dimension(self, mock_settings, mock_modal_client):
        """Test embedding dimension."""
        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()

            assert model.embedding_dim == 1024

    @pytest.mark.asyncio
    async def test_load_model(self, mock_settings, mock_modal_client):
        """Test load_model is a no-op for Modal backend."""
        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()
            await model.load_model()  # Should not raise

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, mock_settings, mock_modal_client, sample_image):
        """Test successful embedding generation."""
        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()
            embedding = await model.generate_embedding(sample_image)

            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (1024,)
            # Verify normalized
            assert np.isclose(np.linalg.norm(embedding), 1.0, atol=0.01)

    @pytest.mark.asyncio
    async def test_generate_embedding_from_bytes(self, mock_settings, mock_modal_client, sample_image_bytes):
        """Test embedding generation from bytes."""
        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()
            embedding = await model.generate_embedding(sample_image_bytes)

            assert isinstance(embedding, np.ndarray)

    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, mock_settings, mock_modal_client, sample_image):
        """Test embedding generation failure."""
        mock_modal_client.megadescriptor_b_embedding.return_value = {
            "success": False,
            "error": "Model inference failed"
        }

        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()

            with pytest.raises(RuntimeError, match="Modal embedding generation failed"):
                await model.generate_embedding(sample_image)

    @pytest.mark.asyncio
    async def test_generate_embedding_queued(self, mock_settings, mock_modal_client, sample_image):
        """Test handling of queued requests."""
        mock_modal_client.megadescriptor_b_embedding.return_value = {
            "success": False,
            "queued": True,
            "error": "Request queued"
        }

        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()

            with pytest.raises(RuntimeError, match="queued"):
                await model.generate_embedding(sample_image)

    def test_compare_embeddings_identical(self, mock_settings, mock_modal_client):
        """Test comparison of identical embeddings."""
        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()
            embedding = np.array([1.0, 0.0, 0.0])
            similarity = model.compare_embeddings(embedding, embedding)

            assert np.isclose(similarity, 1.0)

    def test_compare_embeddings_orthogonal(self, mock_settings, mock_modal_client):
        """Test comparison of orthogonal embeddings."""
        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

            model = MegaDescriptorBReIDModel()
            embedding1 = np.array([1.0, 0.0, 0.0])
            embedding2 = np.array([0.0, 1.0, 0.0])
            similarity = model.compare_embeddings(embedding1, embedding2)

            assert np.isclose(similarity, 0.0)
