"""Tests for CVWC2019ReIDModel."""

import pytest
import numpy as np
from PIL import Image
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.cvwc2019_reid import CVWC2019ReIDModel


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.models.cvwc2019.path = "/path/to/model"
    settings.models.cvwc2019.similarity_threshold = 0.80
    return settings


@pytest.fixture
def mock_modal_client():
    """Mock Modal client for testing."""
    client = MagicMock()
    client.cvwc2019_reid_embedding = AsyncMock()
    return client


@pytest.fixture
def model(mock_settings, mock_modal_client):
    """Create a CVWC2019ReIDModel for testing."""
    with patch('backend.models.cvwc2019_reid.get_settings', return_value=mock_settings), \
         patch('backend.models.cvwc2019_reid.get_modal_client', return_value=mock_modal_client):
        return CVWC2019ReIDModel()


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    return Image.new('RGB', (224, 224), color='blue')


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes."""
    buffer = BytesIO()
    sample_image.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()


class TestCVWC2019ReIDModelInit:
    """Tests for model initialization."""

    def test_init_default(self, mock_settings, mock_modal_client):
        """Test default initialization."""
        with patch('backend.models.cvwc2019_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.cvwc2019_reid.get_modal_client', return_value=mock_modal_client):
            model = CVWC2019ReIDModel()

        assert model.model_path == "/path/to/model"
        assert model.num_classes == 92

    def test_init_custom_params(self, mock_settings, mock_modal_client):
        """Test initialization with custom parameters."""
        with patch('backend.models.cvwc2019_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.cvwc2019_reid.get_modal_client', return_value=mock_modal_client):
            model = CVWC2019ReIDModel(
                model_path="/custom/path",
                config_file="/custom/config.yaml",
                num_classes=100
            )

        assert model.model_path == "/custom/path"
        assert model.config_file == "/custom/config.yaml"
        assert model.num_classes == 100


class TestCVWC2019ReIDModelProperties:
    """Tests for model properties."""

    def test_embedding_dim(self, model):
        """Test embedding dimension is 2048."""
        assert model.embedding_dim == 2048

    def test_similarity_threshold(self, model):
        """Test similarity threshold from settings."""
        assert model.similarity_threshold == 0.80


class TestLoadModel:
    """Tests for model loading."""

    @pytest.mark.asyncio
    async def test_load_model_noop(self, model):
        """Test load_model is a no-op for Modal backend."""
        await model.load_model()  # Should not raise


class TestGenerateEmbedding:
    """Tests for embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, model, sample_image):
        """Test successful embedding generation."""
        mock_embedding = np.random.randn(2048).tolist()
        model.modal_client.cvwc2019_reid_embedding.return_value = {
            "success": True,
            "embedding": mock_embedding
        }

        embedding = await model.generate_embedding(sample_image)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (2048,)
        # Verify normalized
        assert np.isclose(np.linalg.norm(embedding), 1.0)

    @pytest.mark.asyncio
    async def test_generate_embedding_from_bytes(self, model, sample_image_bytes):
        """Test embedding generation from bytes."""
        mock_embedding = np.random.randn(2048).tolist()
        model.modal_client.cvwc2019_reid_embedding.return_value = {
            "success": True,
            "embedding": mock_embedding
        }

        embedding = await model.generate_embedding(sample_image_bytes)

        assert isinstance(embedding, np.ndarray)

    @pytest.mark.asyncio
    async def test_generate_embedding_from_bytes_alias(self, model, sample_image_bytes):
        """Test generate_embedding_from_bytes alias method."""
        mock_embedding = np.random.randn(2048).tolist()
        model.modal_client.cvwc2019_reid_embedding.return_value = {
            "success": True,
            "embedding": mock_embedding
        }

        embedding = await model.generate_embedding_from_bytes(sample_image_bytes)

        assert isinstance(embedding, np.ndarray)

    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, model, sample_image):
        """Test embedding generation failure."""
        model.modal_client.cvwc2019_reid_embedding.return_value = {
            "success": False,
            "error": "Model inference failed"
        }

        with pytest.raises(RuntimeError, match="Modal embedding generation failed"):
            await model.generate_embedding(sample_image)

    @pytest.mark.asyncio
    async def test_generate_embedding_queued(self, model, sample_image):
        """Test handling of queued requests."""
        model.modal_client.cvwc2019_reid_embedding.return_value = {
            "success": False,
            "queued": True,
            "error": "Request queued"
        }

        with pytest.raises(RuntimeError, match="queued"):
            await model.generate_embedding(sample_image)

    @pytest.mark.asyncio
    async def test_generate_embedding_exception(self, model, sample_image):
        """Test handling of exceptions."""
        model.modal_client.cvwc2019_reid_embedding.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            await model.generate_embedding(sample_image)


class TestCompareEmbeddings:
    """Tests for embedding comparison."""

    def test_compare_embeddings_identical(self, model):
        """Test comparison of identical embeddings."""
        embedding = np.array([1.0, 0.0, 0.0])
        similarity = model.compare_embeddings(embedding, embedding)

        assert np.isclose(similarity, 1.0)

    def test_compare_embeddings_orthogonal(self, model):
        """Test comparison of orthogonal embeddings."""
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([0.0, 1.0, 0.0])
        similarity = model.compare_embeddings(embedding1, embedding2)

        assert np.isclose(similarity, 0.0)

    def test_compare_embeddings_flattens_2d(self, model):
        """Test comparison flattens 2D arrays."""
        embedding1 = np.array([[1.0, 0.0, 0.0]])
        embedding2 = np.array([[1.0, 0.0, 0.0]])
        similarity = model.compare_embeddings(embedding1, embedding2)

        assert np.isclose(similarity, 1.0)

    def test_compare_embeddings_error(self, model):
        """Test comparison handles errors."""
        embedding1 = "invalid"
        embedding2 = np.array([1.0, 0.0])

        # Should return 0.0 on error
        similarity = model.compare_embeddings(embedding1, embedding2)
        assert similarity == 0.0

    def test_compare_embeddings_range(self, model):
        """Test similarity is in expected range."""
        np.random.seed(42)
        embedding1 = np.random.randn(2048)
        embedding2 = np.random.randn(2048)
        similarity = model.compare_embeddings(embedding1, embedding2)

        assert -1.0 <= similarity <= 1.0
