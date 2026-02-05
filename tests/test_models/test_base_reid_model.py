"""Tests for BaseReIDModel abstract base class."""

import pytest
import numpy as np
from PIL import Image
from io import BytesIO
from unittest.mock import AsyncMock, patch

from backend.models.interfaces.base_reid_model import BaseReIDModel


class ConcreteReIDModel(BaseReIDModel):
    """Concrete implementation for testing."""

    def __init__(self, embedding_dim: int = 2048, threshold: float = 0.8):
        self._embedding_dim = embedding_dim
        self._threshold = threshold

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    @property
    def similarity_threshold(self) -> float:
        return self._threshold

    async def load_model(self):
        pass

    async def generate_embedding(self, image: Image.Image) -> np.ndarray:
        # Return a mock embedding
        np.random.seed(42)
        embedding = np.random.randn(self._embedding_dim)
        return self.normalize_embedding(embedding)


@pytest.fixture
def model():
    """Create a concrete ReID model for testing."""
    return ConcreteReIDModel()


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = Image.new('RGB', (224, 224), color='red')
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes."""
    buffer = BytesIO()
    sample_image.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()


class TestBaseReIDModelProperties:
    """Tests for BaseReIDModel properties."""

    def test_embedding_dim(self, model):
        """Test embedding dimension property."""
        assert model.embedding_dim == 2048

    def test_custom_embedding_dim(self):
        """Test custom embedding dimension."""
        model = ConcreteReIDModel(embedding_dim=1024)
        assert model.embedding_dim == 1024

    def test_model_name(self, model):
        """Test model name property returns class name."""
        assert model.model_name == "ConcreteReIDModel"

    def test_similarity_threshold_default(self, model):
        """Test default similarity threshold."""
        assert model.similarity_threshold == 0.8

    def test_similarity_threshold_custom(self):
        """Test custom similarity threshold."""
        model = ConcreteReIDModel(threshold=0.9)
        assert model.similarity_threshold == 0.9


class TestNormalizeEmbedding:
    """Tests for embedding normalization."""

    def test_normalize_embedding(self, model):
        """Test embedding normalization to unit length."""
        embedding = np.array([3.0, 4.0])
        normalized = model.normalize_embedding(embedding)

        # Should have unit length
        assert np.isclose(np.linalg.norm(normalized), 1.0)

    def test_normalize_embedding_already_normalized(self, model):
        """Test normalizing already normalized embedding."""
        embedding = np.array([1.0, 0.0, 0.0])
        normalized = model.normalize_embedding(embedding)

        np.testing.assert_array_almost_equal(normalized, embedding)

    def test_normalize_embedding_zero_vector(self, model):
        """Test normalizing zero vector returns zero vector."""
        embedding = np.zeros(100)
        normalized = model.normalize_embedding(embedding)

        np.testing.assert_array_equal(normalized, embedding)

    def test_normalize_embedding_large(self, model):
        """Test normalizing large embedding."""
        embedding = np.random.randn(2048) * 100
        normalized = model.normalize_embedding(embedding)

        assert np.isclose(np.linalg.norm(normalized), 1.0)


class TestComputeSimilarity:
    """Tests for similarity computation."""

    def test_compute_similarity_identical(self, model):
        """Test similarity of identical embeddings is 1.0."""
        embedding = np.array([1.0, 0.0, 0.0])
        similarity = model.compute_similarity(embedding, embedding)

        assert np.isclose(similarity, 1.0)

    def test_compute_similarity_orthogonal(self, model):
        """Test similarity of orthogonal embeddings is 0.0."""
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([0.0, 1.0, 0.0])
        similarity = model.compute_similarity(embedding1, embedding2)

        assert np.isclose(similarity, 0.0)

    def test_compute_similarity_opposite(self, model):
        """Test similarity of opposite embeddings is -1.0."""
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([-1.0, 0.0, 0.0])
        similarity = model.compute_similarity(embedding1, embedding2)

        assert np.isclose(similarity, -1.0)

    def test_compute_similarity_range(self, model):
        """Test similarity is in expected range."""
        embedding1 = np.random.randn(100)
        embedding2 = np.random.randn(100)
        similarity = model.compute_similarity(embedding1, embedding2)

        assert -1.0 <= similarity <= 1.0

    def test_compute_similarity_flattens_2d(self, model):
        """Test similarity flattens 2D embeddings."""
        embedding1 = np.array([[1.0, 0.0, 0.0]])
        embedding2 = np.array([[1.0, 0.0, 0.0]])
        similarity = model.compute_similarity(embedding1, embedding2)

        assert np.isclose(similarity, 1.0)

    def test_compute_similarity_zero_norm(self, model):
        """Test similarity with zero norm vector returns 0.0."""
        embedding1 = np.zeros(100)
        embedding2 = np.random.randn(100)
        similarity = model.compute_similarity(embedding1, embedding2)

        assert similarity == 0.0


class TestGenerateEmbedding:
    """Tests for embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_embedding(self, model, sample_image):
        """Test generating embedding from image."""
        embedding = await model.generate_embedding(sample_image)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (2048,)
        assert np.isclose(np.linalg.norm(embedding), 1.0)

    @pytest.mark.asyncio
    async def test_generate_embedding_from_bytes(self, model, sample_image_bytes):
        """Test generating embedding from image bytes."""
        embedding = await model.generate_embedding_from_bytes(sample_image_bytes)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (2048,)

    @pytest.mark.asyncio
    async def test_generate_embedding_from_bytes_converts_to_rgb(self, model):
        """Test that grayscale images are converted to RGB."""
        # Create grayscale image
        img = Image.new('L', (224, 224), color=128)
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)

        embedding = await model.generate_embedding_from_bytes(buffer.getvalue())

        assert isinstance(embedding, np.ndarray)


class TestBatchGenerateEmbeddings:
    """Tests for batch embedding generation."""

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings(self, model, sample_image):
        """Test batch embedding generation."""
        images = [sample_image, sample_image, sample_image]
        embeddings = await model.batch_generate_embeddings(images)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert isinstance(emb, np.ndarray)
            assert emb.shape == (2048,)

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_empty(self, model):
        """Test batch with empty list."""
        embeddings = await model.batch_generate_embeddings([])

        assert embeddings == []

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_single(self, model, sample_image):
        """Test batch with single image."""
        embeddings = await model.batch_generate_embeddings([sample_image])

        assert len(embeddings) == 1


class TestIdentify:
    """Tests for identification functionality."""

    @pytest.fixture
    def database_embeddings(self):
        """Create mock database embeddings."""
        np.random.seed(123)
        return [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
        ]

    @pytest.fixture
    def database_labels(self):
        """Create mock database labels."""
        return ["tiger_1", "tiger_2", "tiger_3"]

    def test_identify_exact_match(self, model, database_embeddings, database_labels):
        """Test identification with exact match."""
        query = np.array([1.0, 0.0, 0.0])
        label, score, top_k = model.identify(
            query, database_embeddings, database_labels
        )

        assert label == "tiger_1"
        assert np.isclose(score, 1.0)
        assert len(top_k) == 1

    def test_identify_k_matches(self, model, database_embeddings, database_labels):
        """Test identification returns k matches."""
        query = np.array([0.5, 0.5, 0.0])
        label, score, top_k = model.identify(
            query, database_embeddings, database_labels, k=3
        )

        assert len(top_k) == 3

    def test_identify_below_threshold(self, model, database_embeddings, database_labels):
        """Test identification below threshold returns None."""
        query = np.array([0.3, 0.3, 0.3])  # Low similarity to all
        label, score, top_k = model.identify(
            query, database_embeddings, database_labels, threshold=0.99
        )

        assert label is None

    def test_identify_custom_threshold(self, model, database_embeddings, database_labels):
        """Test identification with custom threshold."""
        query = np.array([0.9, 0.1, 0.0])  # High similarity to tiger_1
        label, score, top_k = model.identify(
            query, database_embeddings, database_labels, threshold=0.5
        )

        assert label == "tiger_1"
        assert score >= 0.5

    def test_identify_mismatched_lengths(self, model, database_embeddings):
        """Test identification raises error for mismatched lengths."""
        query = np.array([1.0, 0.0, 0.0])
        with pytest.raises(ValueError, match="same length"):
            model.identify(query, database_embeddings, ["tiger_1", "tiger_2"])

    def test_identify_top_k_sorted(self, model, database_embeddings, database_labels):
        """Test top-k results are sorted by similarity."""
        query = np.array([0.5, 0.3, 0.2])
        label, score, top_k = model.identify(
            query, database_embeddings, database_labels, k=3
        )

        # Verify sorted in descending order
        scores = [s for _, s in top_k]
        assert scores == sorted(scores, reverse=True)


class TestLoadModel:
    """Tests for model loading."""

    @pytest.mark.asyncio
    async def test_load_model(self, model):
        """Test load model is callable."""
        await model.load_model()  # Should not raise

    @pytest.mark.asyncio
    async def test_load_model_idempotent(self, model):
        """Test load model can be called multiple times."""
        await model.load_model()
        await model.load_model()  # Should not raise
