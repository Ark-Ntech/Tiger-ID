"""Tests for MatchAnything verification model."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import io


@pytest.fixture
def sample_image():
    """Create a sample PIL image."""
    return Image.new('RGB', (224, 224), color='white')


@pytest.fixture
def sample_image_pair():
    """Create a pair of sample images."""
    img1 = Image.new('RGB', (224, 224), color='white')
    img2 = Image.new('RGB', (224, 224), color='red')
    return img1, img2


class TestMatchAnythingModel:
    """Tests for MatchAnythingModel class."""

    @patch('backend.models.matchanything.MATCHANYTHING_AVAILABLE', True)
    def test_model_initialization_local(self):
        """Test local model initialization."""
        from backend.models.matchanything import MatchAnythingModel

        model = MatchAnythingModel(threshold=0.3, use_modal=False)

        assert model.threshold == 0.3
        assert model.use_modal is False
        assert model.is_available is True

    def test_model_initialization_modal(self):
        """Test modal-based initialization."""
        from backend.models.matchanything import MatchAnythingModel

        model = MatchAnythingModel(threshold=0.2, use_modal=True)

        assert model.threshold == 0.2
        assert model.use_modal is True
        assert model.is_available is True

    @pytest.mark.asyncio
    @patch('backend.models.matchanything.MATCHANYTHING_AVAILABLE', True)
    async def test_load_model_modal(self):
        """Test load_model with Modal (no-op)."""
        from backend.models.matchanything import MatchAnythingModel

        model = MatchAnythingModel(use_modal=True)
        result = await model.load_model()

        assert result is True

    @pytest.mark.asyncio
    @patch('backend.models.matchanything.MATCHANYTHING_AVAILABLE', False)
    async def test_load_model_unavailable(self):
        """Test load_model when transformers unavailable."""
        from backend.models.matchanything import MatchAnythingModel

        model = MatchAnythingModel(use_modal=False)
        result = await model.load_model()

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_candidates_modal(self, sample_image):
        """Test verify_candidates using Modal."""
        from backend.models.matchanything import MatchAnythingModel

        model = MatchAnythingModel(use_modal=True)

        # Mock modal client
        mock_client = MagicMock()
        mock_client.matchanything_verify = AsyncMock(return_value={
            "success": True,
            "num_matches": 150,
            "confidence": 0.85,
            "is_match": True
        })
        model._modal_client = mock_client

        # Test with a single candidate
        candidates = [{"tiger_id": "t1", "similarity": 0.9, "image_path": "/path/to/img.jpg"}]
        result = await model.verify_candidates(sample_image, candidates)

        # Should return verified results
        assert isinstance(result, list)

    def test_model_name(self):
        """Test model name constant."""
        from backend.models.matchanything import MatchAnythingModel

        assert MatchAnythingModel.MODEL_NAME == "zju-community/matchanything_eloftr"
