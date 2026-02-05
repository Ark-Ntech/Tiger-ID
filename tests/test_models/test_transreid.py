"""Tests for TransReIDModel."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from backend.models.transreid import TransReIDModel, create_transreid_model


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    return settings


@pytest.fixture
def model(mock_settings):
    """Create a TransReIDModel for testing."""
    with patch('backend.models.transreid.get_settings', return_value=mock_settings):
        return TransReIDModel()


class TestTransReIDModelInit:
    """Tests for model initialization."""

    def test_init_default(self, mock_settings):
        """Test default initialization."""
        with patch('backend.models.transreid.get_settings', return_value=mock_settings):
            model = TransReIDModel()

        assert model.model_variant == "vit_base"
        assert model.use_sie is True
        assert model.use_jpm is True
        assert model.embedding_dim == 768

    def test_init_custom_params(self, mock_settings):
        """Test initialization with custom parameters."""
        with patch('backend.models.transreid.get_settings', return_value=mock_settings):
            model = TransReIDModel(
                model_variant="vit_small",
                use_sie=False,
                use_jpm=False
            )

        assert model.model_variant == "vit_small"
        assert model.use_sie is False
        assert model.use_jpm is False

    def test_embedding_dim_base(self, mock_settings):
        """Test embedding dimension for base variant."""
        with patch('backend.models.transreid.get_settings', return_value=mock_settings):
            model = TransReIDModel(model_variant="vit_base")

        assert model.embedding_dim == 768

    def test_embedding_dim_small(self, mock_settings):
        """Test embedding dimension for small variant."""
        with patch('backend.models.transreid.get_settings', return_value=mock_settings):
            model = TransReIDModel(model_variant="vit_small")

        assert model.embedding_dim == 384

    def test_embedding_dim_deit_base(self, mock_settings):
        """Test embedding dimension for deit_base variant."""
        with patch('backend.models.transreid.get_settings', return_value=mock_settings):
            model = TransReIDModel(model_variant="deit_base")

        assert model.embedding_dim == 768


class TestGetModalModel:
    """Tests for Modal model connection."""

    def test_get_modal_model_success(self, model):
        """Test successful Modal connection."""
        mock_cls = MagicMock()

        with patch('modal.Cls.from_name', return_value=mock_cls):
            result = model._get_modal_model()

        assert result == mock_cls
        # Second call should use cached version
        assert model._model_cls == mock_cls

    def test_get_modal_model_cached(self, model):
        """Test Modal model is cached."""
        mock_cls = MagicMock()
        model._model_cls = mock_cls

        result = model._get_modal_model()

        assert result == mock_cls

    def test_get_modal_model_failure(self, model):
        """Test handling of Modal connection failure."""
        with patch('modal.Cls.from_name', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                model._get_modal_model()


class TestGenerateEmbedding:
    """Tests for embedding generation."""

    def test_generate_embedding_success(self, model):
        """Test successful embedding generation."""
        mock_embedding = np.random.randn(768).tolist()
        mock_model_instance = MagicMock()
        mock_model_instance.generate_embedding.remote.return_value = {
            "embedding": mock_embedding,
            "success": True
        }
        mock_cls = MagicMock(return_value=mock_model_instance)
        model._model_cls = mock_cls

        result = model.generate_embedding(b"fake_image_bytes")

        assert result["success"] is True
        assert result["embedding"] == mock_embedding

    def test_generate_embedding_failure(self, model):
        """Test embedding generation failure."""
        mock_cls = MagicMock()
        mock_cls().generate_embedding.remote.side_effect = Exception("Inference failed")
        model._model_cls = mock_cls

        result = model.generate_embedding(b"fake_image_bytes")

        assert result["success"] is False
        assert "error" in result


class TestGenerateEmbeddingBatch:
    """Tests for batch embedding generation."""

    def test_generate_embedding_batch_success(self, model):
        """Test successful batch embedding generation."""
        mock_results = [
            {"embedding": np.random.randn(768).tolist(), "success": True},
            {"embedding": np.random.randn(768).tolist(), "success": True},
        ]
        mock_model_instance = MagicMock()
        mock_model_instance.generate_embedding_batch.remote.return_value = mock_results
        mock_cls = MagicMock(return_value=mock_model_instance)
        model._model_cls = mock_cls

        result = model.generate_embedding_batch([b"image1", b"image2"])

        assert len(result) == 2
        assert all(r["success"] for r in result)

    def test_generate_embedding_batch_failure(self, model):
        """Test batch embedding generation failure."""
        mock_cls = MagicMock()
        mock_cls().generate_embedding_batch.remote.side_effect = Exception("Batch failed")
        model._model_cls = mock_cls

        images = [b"image1", b"image2"]
        result = model.generate_embedding_batch(images)

        assert len(result) == 2
        assert all(not r["success"] for r in result)


class TestComputeSimilarity:
    """Tests for similarity computation."""

    def test_compute_similarity_identical(self, model):
        """Test similarity of identical embeddings."""
        embedding = np.array([1.0, 0.0, 0.0])
        gallery = np.array([[1.0, 0.0, 0.0]])

        similarity = model.compute_similarity(embedding, gallery)

        assert np.isclose(similarity[0], 1.0)

    def test_compute_similarity_orthogonal(self, model):
        """Test similarity of orthogonal embeddings."""
        embedding = np.array([1.0, 0.0, 0.0])
        gallery = np.array([[0.0, 1.0, 0.0]])

        similarity = model.compute_similarity(embedding, gallery)

        assert np.isclose(similarity[0], 0.0)

    def test_compute_similarity_multiple(self, model):
        """Test similarity with multiple gallery items."""
        embedding = np.array([1.0, 0.0, 0.0])
        gallery = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.5, 0.5, 0.0],
        ])

        similarities = model.compute_similarity(embedding, gallery)

        assert len(similarities) == 3
        assert np.isclose(similarities[0], 1.0)
        assert np.isclose(similarities[1], 0.0)

    def test_compute_similarity_normalized(self, model):
        """Test similarity handles unnormalized embeddings."""
        embedding = np.array([3.0, 4.0, 0.0])  # Not normalized
        gallery = np.array([[1.0, 0.0, 0.0]])

        similarity = model.compute_similarity(embedding, gallery)

        # Should still work due to internal normalization
        assert 0.0 <= similarity[0] <= 1.0


class TestGetModelInfo:
    """Tests for model info retrieval."""

    def test_get_model_info(self, model):
        """Test getting model information."""
        info = model.get_model_info()

        assert info["name"] == "TransReID"
        assert info["variant"] == "vit_base"
        assert info["embedding_dim"] == 768
        assert info["use_sie"] is True
        assert info["use_jpm"] is True
        assert info["architecture"] == "Vision Transformer"
        assert info["pretrained"] == "ImageNet-21K"


class TestFactoryFunction:
    """Tests for create_transreid_model factory function."""

    def test_create_transreid_model_default(self, mock_settings):
        """Test factory with default parameters."""
        with patch('backend.models.transreid.get_settings', return_value=mock_settings):
            model = create_transreid_model()

        assert isinstance(model, TransReIDModel)
        assert model.model_variant == "vit_base"

    def test_create_transreid_model_custom(self, mock_settings):
        """Test factory with custom parameters."""
        with patch('backend.models.transreid.get_settings', return_value=mock_settings):
            model = create_transreid_model(
                variant="vit_small",
                use_sie=False,
                use_jpm=False
            )

        assert model.model_variant == "vit_small"
        assert model.use_sie is False
        assert model.use_jpm is False
