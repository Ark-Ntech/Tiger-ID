"""Tests for specific Modal client implementations."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from PIL import Image
import numpy as np
import io

from backend.infrastructure.modal.base_client import (
    BaseModalClient,
    ModalClientError,
    ModalUnavailableError,
)


# ============================================================================
# WildlifeTools Client Tests
# ============================================================================


class TestWildlifeToolsClient:
    """Tests specific to WildlifeToolsClient."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image."""
        return Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

    def test_embedding_dimension_constant(self):
        """Test that embedding dimension is correctly set."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        assert WildlifeToolsClient.EMBEDDING_DIM == 1536

    def test_app_and_class_names(self):
        """Test that app and class names are correct."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "WildlifeToolsModel"

    @pytest.mark.asyncio
    async def test_generate_embedding_mock_mode(self, sample_image):
        """Test embedding generation in mock mode."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert len(result["embedding"]) == 1536
        assert result["shape"] == (1536,)
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_generate_embedding_converts_to_jpeg(self, sample_image):
        """Test that image is converted to JPEG bytes."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        captured_bytes = None

        async def capture_call(method_name, *args, **kwargs):
            nonlocal captured_bytes
            # The first positional arg after method_name should be image bytes
            captured_bytes = args[0] if args else None
            return {"success": True, "embedding": [0.0] * 1536}

        client._call_with_retry = capture_call

        await client.generate_embedding(sample_image)

        assert captured_bytes is not None
        assert isinstance(captured_bytes, bytes)
        # Verify it's valid JPEG by loading it
        loaded_img = Image.open(io.BytesIO(captured_bytes))
        assert loaded_img.format == 'JPEG'

    @pytest.mark.asyncio
    async def test_fallback_on_modal_error(self, sample_image):
        """Test fallback to mock on Modal error."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        async def fail_call(*args, **kwargs):
            raise ModalClientError("Modal error")

        client._call_with_retry = fail_call

        result = await client.generate_embedding(sample_image)

        # Should fall back to mock
        assert result["success"] is True
        assert result["mock"] is True
        assert len(result["embedding"]) == 1536

    def test_singleton_function(self):
        """Test singleton getter function."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import (
            get_wildlife_tools_client,
            WildlifeToolsClient
        )

        client = get_wildlife_tools_client()
        assert isinstance(client, WildlifeToolsClient)


# ============================================================================
# CVWC2019 Client Tests
# ============================================================================


class TestCVWC2019Client:
    """Tests specific to CVWC2019Client."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image."""
        return Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

    def test_embedding_dimension_constant(self):
        """Test that embedding dimension is correctly set."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        assert CVWC2019Client.EMBEDDING_DIM == 2048

    def test_app_and_class_names(self):
        """Test that app and class names are correct."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client

        client = CVWC2019Client(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "CVWC2019ReIDModel"

    @pytest.mark.asyncio
    async def test_generate_embedding_mock_mode(self, sample_image):
        """Test embedding generation in mock mode."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client

        client = CVWC2019Client(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert len(result["embedding"]) == 2048
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_generate_embedding_production_mode(self, sample_image):
        """Test embedding generation in production mode."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client

        client = CVWC2019Client(use_mock=False)

        async def mock_call(*args, **kwargs):
            return {
                "success": True,
                "embedding": [0.1] * 2048,
                "mock": False
            }

        client._call_with_retry = mock_call

        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert len(result["embedding"]) == 2048
        assert result.get("mock") is False

    @pytest.mark.asyncio
    async def test_fallback_on_unavailable_error(self, sample_image):
        """Test fallback on ModalUnavailableError."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client

        client = CVWC2019Client(use_mock=False)

        async def fail_call(*args, **kwargs):
            raise ModalUnavailableError("Service unavailable")

        client._call_with_retry = fail_call

        result = await client.generate_embedding(sample_image)

        # Should fall back to mock
        assert result["success"] is True
        assert result["mock"] is True

    def test_singleton_function(self):
        """Test singleton getter function."""
        from backend.infrastructure.modal.clients.cvwc2019_client import (
            get_cvwc2019_client,
            CVWC2019Client
        )

        client = get_cvwc2019_client()
        assert isinstance(client, CVWC2019Client)


# ============================================================================
# TransReID Client Tests
# ============================================================================


class TestTransReIDClient:
    """Tests specific to TransReIDClient."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image."""
        return Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

    def test_embedding_dimension_constant(self):
        """Test that embedding dimension is correctly set."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        assert TransReIDClient.EMBEDDING_DIM == 768

    def test_app_and_class_names(self):
        """Test that app and class names are correct."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient

        client = TransReIDClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "TransReIDModel"

    @pytest.mark.asyncio
    async def test_generate_embedding_mock_mode(self, sample_image):
        """Test embedding generation in mock mode."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient

        client = TransReIDClient(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert len(result["embedding"]) == 768
        assert result["shape"] == (768,)
        assert result["mock"] is True
        assert "model_info" in result
        assert result["model_info"]["architecture"] == "TransReID"
        assert result["model_info"]["backbone"] == "ViT-Base-Patch16-224"

    @pytest.mark.asyncio
    async def test_generate_embedding_calls_correct_method(self, sample_image):
        """Test that generate_embedding calls the correct Modal method."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient

        client = TransReIDClient(use_mock=False)

        method_called = None

        async def capture_method(method_name, *args, **kwargs):
            nonlocal method_called
            method_called = method_name
            return {"success": True, "embedding": [0.0] * 768}

        client._call_with_retry = capture_method

        await client.generate_embedding(sample_image)

        assert method_called == "generate_embedding"

    @pytest.mark.asyncio
    async def test_fallback_preserves_model_info(self, sample_image):
        """Test that fallback to mock preserves model info."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient

        client = TransReIDClient(use_mock=False)

        async def fail_call(*args, **kwargs):
            raise ModalClientError("Error")

        client._call_with_retry = fail_call

        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert result["mock"] is True
        assert "model_info" in result

    def test_singleton_function(self):
        """Test singleton getter function."""
        from backend.infrastructure.modal.clients.transreid_client import (
            get_transreid_client,
            TransReIDClient
        )

        client = get_transreid_client()
        assert isinstance(client, TransReIDClient)


# ============================================================================
# MegaDescriptor-B Client Tests
# ============================================================================


class TestMegaDescriptorBClient:
    """Tests specific to MegaDescriptorBClient."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image."""
        return Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

    def test_embedding_dimension_constant(self):
        """Test that embedding dimension is correctly set."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
        assert MegaDescriptorBClient.EMBEDDING_DIM == 1024

    def test_app_and_class_names(self):
        """Test that app and class names are correct."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient

        client = MegaDescriptorBClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "MegaDescriptorBModel"

    @pytest.mark.asyncio
    async def test_generate_embedding_mock_mode(self, sample_image):
        """Test embedding generation in mock mode."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient

        client = MegaDescriptorBClient(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert len(result["embedding"]) == 1024
        assert result["shape"] == (1024,)
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_generate_embedding_with_different_dim(self, sample_image):
        """Test that embedding dimension matches class constant."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient

        client = MegaDescriptorBClient(use_mock=True)
        result = await client.generate_embedding(sample_image)

        # Verify dimension matches constant
        assert len(result["embedding"]) == MegaDescriptorBClient.EMBEDDING_DIM

    @pytest.mark.asyncio
    async def test_fallback_respects_embedding_dim(self, sample_image):
        """Test that fallback uses correct embedding dimension."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient

        client = MegaDescriptorBClient(use_mock=False)

        async def fail_call(*args, **kwargs):
            raise ModalClientError("Error")

        client._call_with_retry = fail_call

        result = await client.generate_embedding(sample_image)

        # Fallback should use correct dimension
        assert len(result["embedding"]) == 1024

    def test_singleton_function(self):
        """Test singleton getter function."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import (
            get_megadescriptor_b_client,
            MegaDescriptorBClient
        )

        client = get_megadescriptor_b_client()
        assert isinstance(client, MegaDescriptorBClient)


# ============================================================================
# MatchAnything Client Tests
# ============================================================================


class TestMatchAnythingClientImplementation:
    """Tests specific to MatchAnythingClient implementation."""

    @pytest.fixture
    def sample_images(self):
        """Create two sample images."""
        img1 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img2 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        return img1, img2

    def test_app_and_class_names(self):
        """Test that app and class names are correct."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "MatchAnythingModel"

    @pytest.mark.asyncio
    async def test_match_images_mock_mode(self, sample_images):
        """Test image matching in mock mode."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)
        img1, img2 = sample_images

        result = await client.match_images(img1, img2)

        assert result["success"] is True
        assert "num_matches" in result
        assert "mean_score" in result
        assert "max_score" in result
        assert "min_score" in result
        assert "total_score" in result
        assert result["mock"] is True
        assert isinstance(result["num_matches"], int)
        assert result["num_matches"] >= 0

    @pytest.mark.asyncio
    async def test_match_images_default_threshold(self, sample_images):
        """Test that default threshold is used."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)
        img1, img2 = sample_images

        captured_threshold = None

        async def capture_call(method_name, *args, **kwargs):
            nonlocal captured_threshold
            if len(args) >= 3:
                captured_threshold = args[2]
            return {"success": True, "num_matches": 100}

        client._call_with_retry = capture_call

        await client.match_images(img1, img2)

        # Default threshold should be 0.2
        assert captured_threshold == 0.2

    @pytest.mark.asyncio
    async def test_match_images_custom_threshold(self, sample_images):
        """Test custom threshold parameter."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)
        img1, img2 = sample_images

        captured_threshold = None

        async def capture_call(method_name, *args, **kwargs):
            nonlocal captured_threshold
            if len(args) >= 3:
                captured_threshold = args[2]
            return {"success": True, "num_matches": 50}

        client._call_with_retry = capture_call

        await client.match_images(img1, img2, threshold=0.75)

        assert captured_threshold == 0.75

    @pytest.mark.asyncio
    async def test_match_images_bytes_mock_mode(self):
        """Test matching with bytes input in mock mode."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)

        img1_bytes = b"fake_image_1"
        img2_bytes = b"fake_image_2"

        result = await client.match_images_bytes(img1_bytes, img2_bytes)

        assert result["success"] is True
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_match_images_bytes_production_mode(self):
        """Test matching with bytes input in production mode."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)

        img1_bytes = b"image_data_1"
        img2_bytes = b"image_data_2"

        async def mock_call(method_name, *args, **kwargs):
            return {
                "success": True,
                "num_matches": 75,
                "mean_score": 0.65
            }

        client._call_with_retry = mock_call

        result = await client.match_images_bytes(img1_bytes, img2_bytes, threshold=0.3)

        assert result["success"] is True
        assert result["num_matches"] == 75

    @pytest.mark.asyncio
    async def test_match_images_converts_pil_to_bytes(self, sample_images):
        """Test that PIL images are converted to bytes."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)
        img1, img2 = sample_images

        captured_args = []

        async def capture_call(method_name, *args, **kwargs):
            captured_args.extend(args)
            return {"success": True, "num_matches": 100}

        client._call_with_retry = capture_call

        await client.match_images(img1, img2)

        # First two args should be bytes
        assert len(captured_args) >= 2
        assert isinstance(captured_args[0], bytes)
        assert isinstance(captured_args[1], bytes)

    @pytest.mark.asyncio
    async def test_match_images_fallback_on_error(self, sample_images):
        """Test fallback to mock on error."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)
        img1, img2 = sample_images

        async def fail_call(*args, **kwargs):
            raise ModalClientError("Matching failed")

        client._call_with_retry = fail_call

        result = await client.match_images(img1, img2)

        # Should fall back to mock
        assert result["mock"] is True
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_health_check_mock_response(self):
        """Test health check mock response."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)

        result = await client.health_check()

        assert result["status"] == "mock"
        assert result["model_name"] == "MatchAnything"

    @pytest.mark.asyncio
    async def test_health_check_production_success(self):
        """Test successful health check in production."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)

        async def mock_health(*args, **kwargs):
            return {
                "status": "healthy",
                "model": "MatchAnything-ELOFTR",
                "version": "1.0"
            }

        client._call_with_retry = mock_health

        result = await client.health_check()

        assert result["status"] == "healthy"
        assert "model" in result

    @pytest.mark.asyncio
    async def test_health_check_production_failure(self):
        """Test health check failure in production."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)

        async def fail_health(*args, **kwargs):
            raise ConnectionError("Cannot connect to model")

        client._call_with_retry = fail_health

        result = await client.health_check()

        assert result["status"] == "error"
        assert "error" in result
        assert "Cannot connect" in str(result["error"])

    def test_singleton_function(self):
        """Test singleton getter function."""
        from backend.infrastructure.modal.clients.matchanything_client import (
            get_matchanything_client,
            MatchAnythingClient
        )

        client = get_matchanything_client()
        assert isinstance(client, MatchAnythingClient)


# ============================================================================
# Cross-Client Consistency Tests
# ============================================================================


class TestCrossClientConsistency:
    """Test consistency across different client implementations."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image."""
        return Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

    @pytest.mark.asyncio
    async def test_all_reid_clients_return_embeddings(self, sample_image):
        """Test that all ReID clients return embeddings with correct structure."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient

        clients = [
            (WildlifeToolsClient(use_mock=True), 1536),
            (CVWC2019Client(use_mock=True), 2048),
            (TransReIDClient(use_mock=True), 768),
            (MegaDescriptorBClient(use_mock=True), 1024),
        ]

        for client, expected_dim in clients:
            result = await client.generate_embedding(sample_image)

            assert result["success"] is True
            assert "embedding" in result
            assert len(result["embedding"]) == expected_dim
            assert isinstance(result["embedding"], list)

    def test_all_clients_use_same_app_name(self):
        """Test that all clients use the same Modal app name."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        clients = [
            WildlifeToolsClient(use_mock=True),
            CVWC2019Client(use_mock=True),
            TransReIDClient(use_mock=True),
            MegaDescriptorBClient(use_mock=True),
            MatchAnythingClient(use_mock=True),
        ]

        app_names = [client.app_name for client in clients]

        # All should use the same app name
        assert all(name == "tiger-id-models" for name in app_names)

    def test_all_clients_have_unique_class_names(self):
        """Test that all clients have unique class names."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        clients = [
            WildlifeToolsClient(use_mock=True),
            CVWC2019Client(use_mock=True),
            TransReIDClient(use_mock=True),
            MegaDescriptorBClient(use_mock=True),
            MatchAnythingClient(use_mock=True),
        ]

        class_names = [client.class_name for client in clients]

        # All class names should be unique
        assert len(class_names) == len(set(class_names))

    def test_all_clients_inherit_from_base(self):
        """Test that all client classes inherit from BaseModalClient."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client_classes = [
            WildlifeToolsClient,
            CVWC2019Client,
            TransReIDClient,
            MegaDescriptorBClient,
            MatchAnythingClient,
        ]

        for client_class in client_classes:
            assert issubclass(client_class, BaseModalClient)

    def test_all_clients_support_mock_mode(self):
        """Test that all clients support mock mode."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        clients = [
            WildlifeToolsClient(use_mock=True),
            CVWC2019Client(use_mock=True),
            TransReIDClient(use_mock=True),
            MegaDescriptorBClient(use_mock=True),
            MatchAnythingClient(use_mock=True),
        ]

        for client in clients:
            assert client.use_mock is True

    def test_all_clients_have_stats_tracking(self):
        """Test that all clients have statistics tracking."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        clients = [
            WildlifeToolsClient(use_mock=True),
            CVWC2019Client(use_mock=True),
            TransReIDClient(use_mock=True),
            MegaDescriptorBClient(use_mock=True),
            MatchAnythingClient(use_mock=True),
        ]

        for client in clients:
            stats = client.get_stats()
            assert "requests_sent" in stats
            assert "requests_succeeded" in stats
            assert "requests_failed" in stats
