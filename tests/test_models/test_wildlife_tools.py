"""Tests for WildlifeToolsReIDModel."""

import pytest
import numpy as np
from PIL import Image
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.wildlife_tools import WildlifeToolsReIDModel


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.models.wildlife_tools.similarity_threshold = 0.85
    return settings


@pytest.fixture
def mock_modal_client():
    """Mock Modal client for testing."""
    client = MagicMock()
    client.wildlife_tools_embedding = AsyncMock()
    return client


@pytest.fixture
def model(mock_settings, mock_modal_client):
    """Create a WildlifeToolsReIDModel for testing."""
    with patch('backend.models.wildlife_tools.get_settings', return_value=mock_settings), \
         patch('backend.models.wildlife_tools.get_modal_client', return_value=mock_modal_client):
        return WildlifeToolsReIDModel()


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    return Image.new('RGB', (224, 224), color='green')


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes."""
    buffer = BytesIO()
    sample_image.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()


class TestWildlifeToolsReIDModelInit:
    """Tests for model initialization."""

    def test_init_default(self, mock_settings, mock_modal_client):
        """Test default initialization."""
        with patch('backend.models.wildlife_tools.get_settings', return_value=mock_settings), \
             patch('backend.models.wildlife_tools.get_modal_client', return_value=mock_modal_client):
            model = WildlifeToolsReIDModel()

        assert model.model_type == "megadescriptor"
        assert model.batch_size == 128

    def test_init_custom_params(self, mock_settings, mock_modal_client):
        """Test initialization with custom parameters."""
        with patch('backend.models.wildlife_tools.get_settings', return_value=mock_settings), \
             patch('backend.models.wildlife_tools.get_modal_client', return_value=mock_modal_client):
            model = WildlifeToolsReIDModel(
                model_name="custom_model",
                model_type="wildfusion",
                batch_size=64
            )

        assert model.model_type == "wildfusion"
        assert model.batch_size == 64


class TestWildlifeToolsReIDModelProperties:
    """Tests for model properties."""

    def test_embedding_dim(self, model):
        """Test embedding dimension is 1536."""
        assert model.embedding_dim == 1536

    def test_similarity_threshold(self, model):
        """Test similarity threshold from settings."""
        assert model.similarity_threshold == 0.85


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
        mock_embedding = np.random.randn(1536).tolist()
        model.modal_client.wildlife_tools_embedding.return_value = {
            "success": True,
            "embedding": mock_embedding
        }

        embedding = await model.generate_embedding(sample_image)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1536,)
        # Verify normalized
        assert np.isclose(np.linalg.norm(embedding), 1.0)

    @pytest.mark.asyncio
    async def test_generate_embedding_from_bytes(self, model, sample_image_bytes):
        """Test embedding generation from bytes."""
        mock_embedding = np.random.randn(1536).tolist()
        model.modal_client.wildlife_tools_embedding.return_value = {
            "success": True,
            "embedding": mock_embedding
        }

        embedding = await model.generate_embedding(sample_image_bytes)

        assert isinstance(embedding, np.ndarray)

    @pytest.mark.asyncio
    async def test_generate_embedding_converts_rgba(self, model):
        """Test RGBA images are converted to RGB."""
        rgba_image = Image.new('RGBA', (224, 224), color=(255, 0, 0, 128))
        mock_embedding = np.random.randn(1536).tolist()
        model.modal_client.wildlife_tools_embedding.return_value = {
            "success": True,
            "embedding": mock_embedding
        }

        embedding = await model.generate_embedding(rgba_image)

        assert isinstance(embedding, np.ndarray)

    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, model, sample_image):
        """Test embedding generation failure."""
        model.modal_client.wildlife_tools_embedding.return_value = {
            "success": False,
            "error": "Model inference failed"
        }

        with pytest.raises(RuntimeError, match="Modal embedding generation failed"):
            await model.generate_embedding(sample_image)

    @pytest.mark.asyncio
    async def test_generate_embedding_queued(self, model, sample_image):
        """Test handling of queued requests."""
        model.modal_client.wildlife_tools_embedding.return_value = {
            "success": False,
            "queued": True,
            "error": "Request queued"
        }

        with pytest.raises(RuntimeError, match="queued"):
            await model.generate_embedding(sample_image)

    @pytest.mark.asyncio
    async def test_generate_embedding_exception(self, model, sample_image):
        """Test handling of exceptions."""
        model.modal_client.wildlife_tools_embedding.side_effect = Exception("Network error")

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


class TestIdentify:
    """Tests for identification functionality."""

    def test_identify_best_match(self, model):
        """Test identification returns best match."""
        query = np.array([1.0, 0.0, 0.0])
        database_embeddings = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
        ]
        database_labels = ["tiger_1", "tiger_2"]

        label, score = model.identify(query, database_embeddings, database_labels)

        assert label == "tiger_1"
        assert np.isclose(score, 1.0)

    def test_identify_k_nearest(self, model):
        """Test identification with k neighbors."""
        query = np.array([0.7, 0.3, 0.0])
        database_embeddings = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.5, 0.5, 0.0]),
            np.array([0.0, 1.0, 0.0]),
        ]
        database_labels = ["tiger_1", "tiger_2", "tiger_3"]

        label, score = model.identify(query, database_embeddings, database_labels, k=2)

        assert label in database_labels

    def test_identify_error(self, model):
        """Test identification handles errors."""
        query = np.array([1.0, 0.0])
        database_embeddings = ["invalid"]
        database_labels = ["tiger_1"]

        label, score = model.identify(query, database_embeddings, database_labels)

        # When compare_embeddings errors, it returns 0.0 but identify still returns the best match
        assert label == "tiger_1"
        assert score == 0.0
