"""Tests for Modal client base class and implementations."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from PIL import Image
import numpy as np
import io

from backend.infrastructure.modal.base_client import (
    BaseModalClient,
    ModalClientError,
    ModalUnavailableError,
)


# ============================================================================
# BaseModalClient Tests
# ============================================================================


class TestBaseModalClient:
    """Test suite for BaseModalClient base class."""

    def test_default_initialization(self):
        """Test that BaseModalClient initializes with correct default values."""
        # Create a concrete implementation for testing
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()

        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert client.timeout == 120
        assert client.stats["requests_sent"] == 0
        assert client.stats["requests_succeeded"] == 0
        assert client.stats["requests_failed"] == 0
        assert client._modal_function is None

    def test_custom_initialization(self):
        """Test BaseModalClient with custom parameters."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(
            max_retries=5,
            retry_delay=2.0,
            timeout=60
        )

        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.timeout == 60

    def test_mock_mode_via_parameter(self):
        """Test that mock mode can be enabled via parameter."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(use_mock=True)
        assert client.use_mock is True

    def test_mock_mode_via_environment(self):
        """Test that mock mode can be enabled via environment variable."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        with patch.dict('os.environ', {'MODAL_USE_MOCK': 'true'}):
            client = ConcreteClient()
            assert client.use_mock is True

    def test_get_stats(self):
        """Test that get_stats returns a copy of statistics."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()
        stats1 = client.get_stats()
        stats2 = client.get_stats()

        # Should be equal but not the same object
        assert stats1 == stats2
        assert stats1 is not stats2

        # Modifying returned stats shouldn't affect internal stats
        stats1["requests_sent"] = 999
        assert client.get_stats()["requests_sent"] == 0

    def test_reset_stats(self):
        """Test that reset_stats clears all statistics."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()

        # Manually set some stats
        client.stats["requests_sent"] = 10
        client.stats["requests_succeeded"] = 8
        client.stats["requests_failed"] = 2

        # Reset and verify
        client.reset_stats()
        assert client.stats["requests_sent"] == 0
        assert client.stats["requests_succeeded"] == 0
        assert client.stats["requests_failed"] == 0

    @pytest.mark.asyncio
    async def test_call_with_retry_success_first_attempt(self):
        """Test successful call on first attempt."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()

        # Mock the Modal function
        mock_method = AsyncMock(return_value={"success": True})
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method

        client._modal_function = mock_modal_func

        # Make the call
        result = await client._call_with_retry("test_method", "arg1", kwarg1="value1")

        assert result == {"success": True}
        assert client.stats["requests_sent"] == 1
        assert client.stats["requests_succeeded"] == 1
        assert client.stats["requests_failed"] == 0
        mock_method.assert_called_once_with("arg1", kwarg1="value1")

    @pytest.mark.asyncio
    async def test_call_with_retry_success_after_failures(self):
        """Test successful call after initial failures with retry."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=3, retry_delay=0.1)

        # Mock the Modal function to fail twice then succeed
        mock_method = AsyncMock(side_effect=[
            Exception("Error 1"),
            Exception("Error 2"),
            {"success": True}
        ])
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method

        client._modal_function = mock_modal_func

        # Make the call
        result = await client._call_with_retry("test_method")

        assert result == {"success": True}
        assert client.stats["requests_sent"] == 3
        assert client.stats["requests_succeeded"] == 1
        assert client.stats["requests_failed"] == 0
        assert mock_method.call_count == 3

    @pytest.mark.asyncio
    async def test_call_with_retry_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=3, retry_delay=0.1)

        # Mock the Modal function to always fail
        mock_method = AsyncMock(side_effect=Exception("Always fails"))
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method

        client._modal_function = mock_modal_func

        # Track sleep calls to verify exponential backoff
        sleep_calls = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            sleep_calls.append(delay)
            # Use a very short actual sleep to speed up test
            await original_sleep(0.001)

        with patch('asyncio.sleep', side_effect=mock_sleep):
            with pytest.raises(ModalClientError):
                await client._call_with_retry("test_method")

        # Should have 2 sleep calls (one less than max_retries)
        assert len(sleep_calls) == 2
        # Verify exponential backoff: 0.1 * 2^0 = 0.1, 0.1 * 2^1 = 0.2
        assert sleep_calls[0] == pytest.approx(0.1)
        assert sleep_calls[1] == pytest.approx(0.2)

    @pytest.mark.asyncio
    async def test_call_with_retry_all_retries_exhausted(self):
        """Test that ModalClientError is raised after all retries fail."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=3, retry_delay=0.01)

        # Mock the Modal function to always fail
        mock_method = AsyncMock(side_effect=Exception("Always fails"))
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method

        client._modal_function = mock_modal_func

        # Should raise ModalClientError after all retries
        with pytest.raises(ModalClientError) as exc_info:
            await client._call_with_retry("test_method")

        assert "Request failed after 3 attempts" in str(exc_info.value)
        assert client.stats["requests_sent"] == 3
        assert client.stats["requests_succeeded"] == 0
        assert client.stats["requests_failed"] == 1

    @pytest.mark.asyncio
    async def test_call_with_retry_timeout_error(self):
        """Test handling of timeout errors."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=2, retry_delay=0.01, timeout=1)

        # Mock the Modal function to timeout
        mock_method = AsyncMock(side_effect=asyncio.TimeoutError("Timeout"))
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method

        client._modal_function = mock_modal_func

        with pytest.raises(ModalClientError):
            await client._call_with_retry("test_method")

        assert client.stats["requests_sent"] == 2
        assert client.stats["requests_failed"] == 1

    def test_get_modal_function_lazy_loading(self):
        """Test that Modal function is loaded lazily."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()

        # Initially None
        assert client._modal_function is None

        # Mock modal.Cls.from_name
        mock_modal_instance = Mock()
        mock_cls = Mock(return_value=mock_modal_instance)

        with patch('modal.Cls.from_name', return_value=mock_cls):
            result = client._get_modal_function()

            assert result is mock_modal_instance
            assert client._modal_function is mock_modal_instance

            # Second call should return cached instance
            result2 = client._get_modal_function()
            assert result2 is mock_modal_instance

    def test_get_modal_function_connection_failure(self):
        """Test handling of Modal connection failure."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()

        # Mock modal.Cls.from_name to raise an exception
        with patch('modal.Cls.from_name', side_effect=Exception("Connection failed")):
            with pytest.raises(ModalUnavailableError) as exc_info:
                client._get_modal_function()

            assert "Failed to connect to Modal" in str(exc_info.value)


# ============================================================================
# Client Inheritance Tests
# ============================================================================


class TestClientInheritance:
    """Test that all client implementations inherit from BaseModalClient."""

    def test_wildlife_tools_inherits_base(self):
        """Test WildlifeToolsClient inherits from BaseModalClient."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        assert issubclass(WildlifeToolsClient, BaseModalClient)

    def test_cvwc2019_inherits_base(self):
        """Test CVWC2019Client inherits from BaseModalClient."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        assert issubclass(CVWC2019Client, BaseModalClient)

    def test_transreid_inherits_base(self):
        """Test TransReIDClient inherits from BaseModalClient."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
        assert issubclass(TransReIDClient, BaseModalClient)

    def test_megadescriptor_b_inherits_base(self):
        """Test MegaDescriptorBClient inherits from BaseModalClient."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
        assert issubclass(MegaDescriptorBClient, BaseModalClient)

    def test_matchanything_inherits_base(self):
        """Test MatchAnythingClient inherits from BaseModalClient."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient
        assert issubclass(MatchAnythingClient, BaseModalClient)


# ============================================================================
# Singleton Pattern Tests
# ============================================================================


class TestClientSingletons:
    """Test that singleton getters return the same instance."""

    def test_wildlife_tools_singleton(self):
        """Test WildlifeToolsClient singleton pattern."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import (
            get_wildlife_tools_client
        )

        client1 = get_wildlife_tools_client()
        client2 = get_wildlife_tools_client()

        assert client1 is client2

    def test_cvwc2019_singleton(self):
        """Test CVWC2019Client singleton pattern."""
        from backend.infrastructure.modal.clients.cvwc2019_client import (
            get_cvwc2019_client
        )

        client1 = get_cvwc2019_client()
        client2 = get_cvwc2019_client()

        assert client1 is client2

    def test_transreid_singleton(self):
        """Test TransReIDClient singleton pattern."""
        from backend.infrastructure.modal.clients.transreid_client import (
            get_transreid_client
        )

        client1 = get_transreid_client()
        client2 = get_transreid_client()

        assert client1 is client2

    def test_megadescriptor_b_singleton(self):
        """Test MegaDescriptorBClient singleton pattern."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import (
            get_megadescriptor_b_client
        )

        client1 = get_megadescriptor_b_client()
        client2 = get_megadescriptor_b_client()

        assert client1 is client2

    def test_matchanything_singleton(self):
        """Test MatchAnythingClient singleton pattern."""
        from backend.infrastructure.modal.clients.matchanything_client import (
            get_matchanything_client
        )

        client1 = get_matchanything_client()
        client2 = get_matchanything_client()

        assert client1 is client2


# ============================================================================
# Client Properties Tests
# ============================================================================


class TestClientProperties:
    """Test that each client has correct properties."""

    def test_wildlife_tools_properties(self):
        """Test WildlifeToolsClient properties."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "WildlifeToolsModel"
        assert client.EMBEDDING_DIM == 1536

    def test_cvwc2019_properties(self):
        """Test CVWC2019Client properties."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client

        client = CVWC2019Client(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "CVWC2019ReIDModel"
        assert client.EMBEDDING_DIM == 2048

    def test_transreid_properties(self):
        """Test TransReIDClient properties."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient

        client = TransReIDClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "TransReIDModel"
        assert client.EMBEDDING_DIM == 768

    def test_megadescriptor_b_properties(self):
        """Test MegaDescriptorBClient properties."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient

        client = MegaDescriptorBClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "MegaDescriptorBModel"
        assert client.EMBEDDING_DIM == 1024

    def test_matchanything_properties(self):
        """Test MatchAnythingClient properties."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)
        assert client.app_name == "tiger-id-models"
        assert client.class_name == "MatchAnythingModel"


# ============================================================================
# Generate Embedding Interface Tests
# ============================================================================


class TestGenerateEmbedding:
    """Test generate_embedding method across all ReID clients."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing."""
        # Create a simple 100x100 RGB image
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        return Image.fromarray(img_array)

    @pytest.mark.asyncio
    async def test_wildlife_tools_generate_embedding_mock(self, sample_image):
        """Test WildlifeToolsClient.generate_embedding in mock mode."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert "embedding" in result
        assert len(result["embedding"]) == 1536
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_cvwc2019_generate_embedding_mock(self, sample_image):
        """Test CVWC2019Client.generate_embedding in mock mode."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client

        client = CVWC2019Client(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert "embedding" in result
        assert len(result["embedding"]) == 2048
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_transreid_generate_embedding_mock(self, sample_image):
        """Test TransReIDClient.generate_embedding in mock mode."""
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient

        client = TransReIDClient(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert "embedding" in result
        assert len(result["embedding"]) == 768
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_megadescriptor_b_generate_embedding_mock(self, sample_image):
        """Test MegaDescriptorBClient.generate_embedding in mock mode."""
        from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient

        client = MegaDescriptorBClient(use_mock=True)
        result = await client.generate_embedding(sample_image)

        assert result["success"] is True
        assert "embedding" in result
        assert len(result["embedding"]) == 1024
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_generate_embedding_fallback_on_error(self, sample_image):
        """Test that clients fall back to mock on Modal error."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        # Mock _call_with_retry to raise an error
        async def mock_call_with_retry(*args, **kwargs):
            raise ModalClientError("Test error")

        client._call_with_retry = mock_call_with_retry

        result = await client.generate_embedding(sample_image)

        # Should fall back to mock response
        assert result["success"] is True
        assert result["mock"] is True
        assert len(result["embedding"]) == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_converts_image_to_bytes(self, sample_image):
        """Test that generate_embedding properly converts PIL Image to bytes."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        # Mock _call_with_retry to capture the image bytes
        captured_args = []

        async def mock_call_with_retry(method_name, *args, **kwargs):
            captured_args.append((method_name, args, kwargs))
            return {"success": True, "embedding": [0.0] * 1536}

        client._call_with_retry = mock_call_with_retry

        result = await client.generate_embedding(sample_image)

        assert len(captured_args) == 1
        assert captured_args[0][0] == "generate_embedding"
        assert len(captured_args[0][1]) == 1
        assert isinstance(captured_args[0][1][0], bytes)


# ============================================================================
# MatchAnything Client Tests
# ============================================================================


class TestMatchAnythingClient:
    """Test MatchAnythingClient specific functionality."""

    @pytest.fixture
    def sample_images(self):
        """Create two sample PIL Images for testing."""
        img1 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img2 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        return img1, img2

    @pytest.mark.asyncio
    async def test_match_images_mock(self, sample_images):
        """Test MatchAnythingClient.match_images in mock mode."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)
        img1, img2 = sample_images

        result = await client.match_images(img1, img2)

        assert result["success"] is True
        assert "num_matches" in result
        assert "mean_score" in result
        assert "max_score" in result
        assert "total_score" in result
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_match_images_with_custom_threshold(self, sample_images):
        """Test MatchAnythingClient.match_images with custom threshold."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)
        img1, img2 = sample_images

        # Mock _call_with_retry to capture threshold
        captured_args = []

        async def mock_call_with_retry(method_name, *args, **kwargs):
            captured_args.append((method_name, args, kwargs))
            return {"success": True, "num_matches": 100}

        client._call_with_retry = mock_call_with_retry

        await client.match_images(img1, img2, threshold=0.5)

        assert len(captured_args) == 1
        assert captured_args[0][1][2] == 0.5  # threshold parameter

    @pytest.mark.asyncio
    async def test_match_images_bytes(self):
        """Test MatchAnythingClient.match_images_bytes method."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)

        # Create image bytes
        img1_bytes = b"fake_image_1"
        img2_bytes = b"fake_image_2"

        result = await client.match_images_bytes(img1_bytes, img2_bytes, threshold=0.3)

        assert result["success"] is True
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_match_images_fallback_on_error(self, sample_images):
        """Test that match_images falls back to mock on error."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)
        img1, img2 = sample_images

        # Mock _call_with_retry to raise an error
        async def mock_call_with_retry(*args, **kwargs):
            raise ModalClientError("Test error")

        client._call_with_retry = mock_call_with_retry

        result = await client.match_images(img1, img2)

        # Should fall back to mock response
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_health_check_mock(self):
        """Test MatchAnythingClient.health_check in mock mode."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)
        result = await client.health_check()

        assert result["status"] == "mock"
        assert result["model_name"] == "MatchAnything"

    @pytest.mark.asyncio
    async def test_health_check_error_handling(self):
        """Test MatchAnythingClient.health_check error handling."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)

        # Mock _call_with_retry to raise an error
        async def mock_call_with_retry(*args, **kwargs):
            raise Exception("Health check failed")

        client._call_with_retry = mock_call_with_retry

        result = await client.health_check()

        assert result["status"] == "error"
        assert "error" in result


# ============================================================================
# Mock Provider Integration Tests
# ============================================================================


class TestMockProviderIntegration:
    """Test integration with MockResponseProvider."""

    def test_mock_provider_wildlife_tools(self):
        """Test MockResponseProvider for WildlifeTools."""
        from backend.infrastructure.modal.mock_provider import MockResponseProvider

        result = MockResponseProvider.wildlife_tools_embedding(1536)

        assert result["success"] is True
        assert len(result["embedding"]) == 1536
        assert result["shape"] == (1536,)
        assert result["mock"] is True

    def test_mock_provider_cvwc2019(self):
        """Test MockResponseProvider for CVWC2019."""
        from backend.infrastructure.modal.mock_provider import MockResponseProvider

        result = MockResponseProvider.cvwc2019_embedding(2048)

        assert result["success"] is True
        assert len(result["embedding"]) == 2048
        assert result["mock"] is True

    def test_mock_provider_transreid(self):
        """Test MockResponseProvider for TransReID."""
        from backend.infrastructure.modal.mock_provider import MockResponseProvider

        result = MockResponseProvider.transreid_embedding()

        assert result["success"] is True
        assert len(result["embedding"]) == 768
        assert result["model_info"]["architecture"] == "TransReID"
        assert result["mock"] is True

    def test_mock_provider_megadescriptor_b(self):
        """Test MockResponseProvider for MegaDescriptor-B."""
        from backend.infrastructure.modal.mock_provider import MockResponseProvider

        result = MockResponseProvider.megadescriptor_b_embedding(1024)

        assert result["success"] is True
        assert len(result["embedding"]) == 1024
        assert result["mock"] is True

    def test_mock_provider_matchanything(self):
        """Test MockResponseProvider for MatchAnything."""
        from backend.infrastructure.modal.mock_provider import MockResponseProvider

        result = MockResponseProvider.matchanything_match(num_matches=100)

        assert result["success"] is True
        assert result["num_matches"] == 100
        assert "mean_score" in result
        assert "max_score" in result
        assert result["mock"] is True

    def test_mock_provider_get_embedding_response(self):
        """Test generic get_embedding_response method."""
        from backend.infrastructure.modal.mock_provider import MockResponseProvider

        result = MockResponseProvider.get_embedding_response("wildlife_tools")

        assert result["success"] is True
        assert result["model"] == "wildlife_tools"
        assert len(result["embedding"]) == 1536
        assert result["mock"] is True


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling across Modal clients."""

    def test_modal_client_error_inheritance(self):
        """Test that ModalClientError is a proper exception."""
        error = ModalClientError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_modal_unavailable_error_inheritance(self):
        """Test that ModalUnavailableError inherits from ModalClientError."""
        error = ModalUnavailableError("Service unavailable")
        assert isinstance(error, ModalClientError)
        assert isinstance(error, Exception)
        assert str(error) == "Service unavailable"

    @pytest.mark.asyncio
    async def test_client_handles_connection_errors(self):
        """Test that clients properly handle connection errors."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        # Create a sample image
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

        # Mock _call_with_retry to raise ModalUnavailableError
        async def mock_call_with_retry(*args, **kwargs):
            raise ModalUnavailableError("Modal is down")

        client._call_with_retry = mock_call_with_retry

        # Should fall back to mock response instead of propagating error
        result = await client.generate_embedding(img)

        assert result["success"] is True
        assert result["mock"] is True


# ============================================================================
# Statistics Tracking Tests
# ============================================================================


class TestStatisticsTracking:
    """Test that clients properly track statistics."""

    @pytest.mark.asyncio
    async def test_stats_tracking_on_success(self):
        """Test that successful requests increment the right counters."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()

        # Mock successful call
        mock_method = AsyncMock(return_value={"success": True})
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method
        client._modal_function = mock_modal_func

        await client._call_with_retry("test_method")

        stats = client.get_stats()
        assert stats["requests_sent"] == 1
        assert stats["requests_succeeded"] == 1
        assert stats["requests_failed"] == 0

    @pytest.mark.asyncio
    async def test_stats_tracking_on_failure(self):
        """Test that failed requests increment the right counters."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=2, retry_delay=0.01)

        # Mock failing call
        mock_method = AsyncMock(side_effect=Exception("Always fails"))
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method
        client._modal_function = mock_modal_func

        with pytest.raises(ModalClientError):
            await client._call_with_retry("test_method")

        stats = client.get_stats()
        assert stats["requests_sent"] == 2
        assert stats["requests_succeeded"] == 0
        assert stats["requests_failed"] == 1

    @pytest.mark.asyncio
    async def test_stats_tracking_with_retries(self):
        """Test stats tracking with multiple retries before success."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=5, retry_delay=0.01)

        # Mock call that succeeds on 3rd attempt
        mock_method = AsyncMock(side_effect=[
            Exception("Fail 1"),
            Exception("Fail 2"),
            {"success": True}
        ])
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method
        client._modal_function = mock_modal_func

        await client._call_with_retry("test_method")

        stats = client.get_stats()
        assert stats["requests_sent"] == 3
        assert stats["requests_succeeded"] == 1
        assert stats["requests_failed"] == 0
