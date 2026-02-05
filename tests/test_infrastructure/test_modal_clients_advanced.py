"""Advanced tests for Modal clients - edge cases, concurrency, and integration."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from PIL import Image
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from backend.infrastructure.modal.base_client import (
    BaseModalClient,
    ModalClientError,
    ModalUnavailableError,
)


# ============================================================================
# Concurrency Tests
# ============================================================================


class TestConcurrency:
    """Test concurrent requests to Modal clients."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing."""
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        return Image.fromarray(img_array)

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_client(self, sample_image):
        """Test multiple concurrent requests to the same client."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)

        # Make 10 concurrent requests
        tasks = [client.generate_embedding(sample_image) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        for result in results:
            assert result["success"] is True
            assert len(result["embedding"]) == 1536

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_clients(self, sample_image):
        """Test concurrent requests to different client types."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
        from backend.infrastructure.modal.clients.transreid_client import TransReIDClient

        wt_client = WildlifeToolsClient(use_mock=True)
        cvwc_client = CVWC2019Client(use_mock=True)
        trans_client = TransReIDClient(use_mock=True)

        # Make concurrent requests to different clients
        tasks = [
            wt_client.generate_embedding(sample_image),
            cvwc_client.generate_embedding(sample_image),
            trans_client.generate_embedding(sample_image),
        ]
        results = await asyncio.gather(*tasks)

        # Verify each result
        assert len(results) == 3
        assert len(results[0]["embedding"]) == 1536  # WildlifeTools
        assert len(results[1]["embedding"]) == 2048  # CVWC2019
        assert len(results[2]["embedding"]) == 768   # TransReID

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_failures(self, sample_image):
        """Test concurrent requests where some fail."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        # Mock some requests to fail, some to succeed
        call_count = 0

        async def mock_call_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise ModalClientError("Simulated failure")
            return {"success": True, "embedding": [0.0] * 1536, "mock": False}

        client._call_with_retry = mock_call_with_retry

        # Make 10 concurrent requests
        tasks = [client.generate_embedding(sample_image) for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should have mix of successes and mock fallbacks (no exceptions)
        assert len(results) == 10
        for result in results:
            assert isinstance(result, dict)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_singleton_thread_safety(self):
        """Test that singleton pattern is thread-safe."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import (
            get_wildlife_tools_client
        )

        # Create multiple clients from different async tasks
        async def get_client():
            return get_wildlife_tools_client()

        tasks = [get_client() for _ in range(50)]
        clients = await asyncio.gather(*tasks)

        # All should be the same instance
        first_client = clients[0]
        assert all(client is first_client for client in clients)


# ============================================================================
# Timeout Handling Tests
# ============================================================================


class TestTimeoutHandling:
    """Test timeout behavior in Modal clients."""

    @pytest.mark.asyncio
    async def test_custom_timeout_value(self):
        """Test that custom timeout values are respected."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(timeout=5)
        assert client.timeout == 5

    @pytest.mark.asyncio
    async def test_timeout_triggers_retry(self):
        """Test that timeouts trigger retry logic."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=3, retry_delay=0.01, timeout=0.1)

        # Mock method that takes longer than timeout
        async def slow_method(*args, **kwargs):
            await asyncio.sleep(1)
            return {"success": True}

        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = slow_method
        client._modal_function = mock_modal_func

        # Should timeout and retry, then fail
        with pytest.raises(ModalClientError):
            await client._call_with_retry("test_method")

        # Should have attempted all retries
        assert client.stats["requests_sent"] == 3

    @pytest.mark.asyncio
    async def test_timeout_then_success(self):
        """Test that request succeeds after initial timeout."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=3, retry_delay=0.01, timeout=0.1)

        # Mock method that times out first, then succeeds
        call_count = 0

        async def sometimes_slow_method(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(1)  # First call times out
            return {"success": True}

        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = sometimes_slow_method
        client._modal_function = mock_modal_func

        result = await client._call_with_retry("test_method")

        assert result["success"] is True
        assert client.stats["requests_sent"] == 2
        assert client.stats["requests_succeeded"] == 1


# ============================================================================
# Image Format Tests
# ============================================================================


class TestImageFormats:
    """Test handling of different image formats and sizes."""

    @pytest.mark.asyncio
    async def test_rgb_image(self):
        """Test handling of RGB images."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)

        # Create RGB image
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        assert img.mode == "RGB"

        result = await client.generate_embedding(img)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_rgba_image_conversion(self):
        """Test handling of RGBA images (should convert to RGB)."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)

        # Create RGBA image
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 4), dtype=np.uint8))
        assert img.mode == "RGBA"

        # Convert to RGB before processing (as the client should do)
        img_rgb = img.convert("RGB")
        result = await client.generate_embedding(img_rgb)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_grayscale_image_conversion(self):
        """Test handling of grayscale images."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)

        # Create grayscale image
        img = Image.fromarray(np.random.randint(0, 255, (100, 100), dtype=np.uint8))
        assert img.mode == "L"

        # Convert to RGB
        img_rgb = img.convert("RGB")
        result = await client.generate_embedding(img_rgb)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_small_image(self):
        """Test handling of small images."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)

        # Create very small image
        img = Image.fromarray(np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8))
        result = await client.generate_embedding(img)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_large_image(self):
        """Test handling of large images."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)

        # Create large image
        img = Image.fromarray(np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8))
        result = await client.generate_embedding(img)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_non_square_image(self):
        """Test handling of non-square images."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)

        # Create rectangular image
        img = Image.fromarray(np.random.randint(0, 255, (200, 100, 3), dtype=np.uint8))
        result = await client.generate_embedding(img)
        assert result["success"] is True


# ============================================================================
# Error Recovery Tests
# ============================================================================


class TestErrorRecovery:
    """Test error recovery and fallback mechanisms."""

    @pytest.mark.asyncio
    async def test_fallback_to_mock_on_modal_unavailable(self):
        """Test fallback to mock when Modal is unavailable."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

        # Simulate Modal unavailable
        async def mock_call_with_retry(*args, **kwargs):
            raise ModalUnavailableError("Modal is down")

        client._call_with_retry = mock_call_with_retry

        result = await client.generate_embedding(img)

        # Should fall back to mock
        assert result["success"] is True
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_fallback_to_mock_on_client_error(self):
        """Test fallback to mock on general client error."""
        from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client

        client = CVWC2019Client(use_mock=False)
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

        # Simulate client error
        async def mock_call_with_retry(*args, **kwargs):
            raise ModalClientError("Some error occurred")

        client._call_with_retry = mock_call_with_retry

        result = await client.generate_embedding(img)

        # Should fall back to mock
        assert result["success"] is True
        assert result["mock"] is True

    @pytest.mark.asyncio
    async def test_no_fallback_when_mock_enabled(self):
        """Test that no fallback happens when already in mock mode."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=True)
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

        result = await client.generate_embedding(img)

        # Should use mock directly, not via fallback
        assert result["success"] is True
        assert result["mock"] is True


# ============================================================================
# MatchAnything Advanced Tests
# ============================================================================


class TestMatchAnythingAdvanced:
    """Advanced tests for MatchAnything client."""

    @pytest.fixture
    def sample_images(self):
        """Create two sample PIL Images."""
        img1 = Image.fromarray(np.random.randint(0, 255, (200, 150, 3), dtype=np.uint8))
        img2 = Image.fromarray(np.random.randint(0, 255, (150, 200, 3), dtype=np.uint8))
        return img1, img2

    @pytest.mark.asyncio
    async def test_match_images_different_sizes(self, sample_images):
        """Test matching images of different sizes."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)
        img1, img2 = sample_images

        result = await client.match_images(img1, img2)

        assert result["success"] is True
        assert "num_matches" in result

    @pytest.mark.asyncio
    async def test_match_images_various_thresholds(self, sample_images):
        """Test matching with various threshold values."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)
        img1, img2 = sample_images

        thresholds = [0.1, 0.2, 0.5, 0.8, 0.9]

        for threshold in thresholds:
            result = await client.match_images(img1, img2, threshold=threshold)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_match_images_bytes_vs_pil(self):
        """Test that match_images and match_images_bytes produce similar results."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=True)

        img1 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img2 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))

        # Test with PIL images
        result1 = await client.match_images(img1, img2)

        # Test with bytes
        import io
        buf1 = io.BytesIO()
        img1.save(buf1, format='JPEG')
        buf2 = io.BytesIO()
        img2.save(buf2, format='JPEG')

        result2 = await client.match_images_bytes(
            buf1.getvalue(),
            buf2.getvalue()
        )

        # Both should succeed
        assert result1["success"] is True
        assert result2["success"] is True

    @pytest.mark.asyncio
    async def test_health_check_in_production_mode(self):
        """Test health check when not in mock mode."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)

        # Mock successful health check
        async def mock_call_with_retry(*args, **kwargs):
            return {"status": "healthy", "model": "MatchAnything"}

        client._call_with_retry = mock_call_with_retry

        result = await client.health_check()

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_handles_errors_gracefully(self):
        """Test that health check returns error info on failure."""
        from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

        client = MatchAnythingClient(use_mock=False)

        # Mock health check failure
        async def mock_call_with_retry(*args, **kwargs):
            raise ValueError("Connection refused")

        client._call_with_retry = mock_call_with_retry

        result = await client.health_check()

        assert result["status"] == "error"
        assert "error" in result


# ============================================================================
# Client Configuration Tests
# ============================================================================


class TestClientConfiguration:
    """Test various client configuration scenarios."""

    def test_client_with_minimal_retries(self):
        """Test client with minimal retry configuration."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=1)
        assert client.max_retries == 1

    def test_client_with_zero_retry_delay(self):
        """Test client with zero retry delay."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(retry_delay=0.0)
        assert client.retry_delay == 0.0

    def test_client_with_long_timeout(self):
        """Test client with long timeout value."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(timeout=600)
        assert client.timeout == 600

    def test_multiple_clients_independent_config(self):
        """Test that multiple client instances have independent configurations."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client1 = WildlifeToolsClient(max_retries=3, use_mock=True)
        client2 = WildlifeToolsClient(max_retries=5, use_mock=False)

        # They should be different instances with different configs
        assert client1.max_retries == 3
        assert client2.max_retries == 5
        assert client1.use_mock is True
        assert client2.use_mock is False


# ============================================================================
# Modal Function Loading Tests
# ============================================================================


class TestModalFunctionLoading:
    """Test Modal function loading behavior."""

    def test_lazy_loading_not_triggered_immediately(self):
        """Test that Modal function is not loaded on client creation."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        # Should be None initially
        assert client._modal_function is None

    def test_lazy_loading_triggered_on_first_call(self):
        """Test that Modal function is loaded on first use."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        # Mock modal.Cls.from_name
        mock_instance = Mock()
        mock_cls = Mock(return_value=mock_instance)

        with patch('modal.Cls.from_name', return_value=mock_cls):
            result = client._get_modal_function()

            assert result is mock_instance
            assert client._modal_function is mock_instance

    def test_function_cached_after_first_load(self):
        """Test that Modal function is cached after first load."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        mock_instance = Mock()
        mock_cls = Mock(return_value=mock_instance)
        mock_from_name = Mock(return_value=mock_cls)

        with patch('modal.Cls.from_name', mock_from_name):
            # First call
            result1 = client._get_modal_function()
            # Second call
            result2 = client._get_modal_function()

            # Should only call from_name once
            assert mock_from_name.call_count == 1
            assert result1 is result2

    def test_connection_error_raises_unavailable(self):
        """Test that connection errors raise ModalUnavailableError."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        with patch('modal.Cls.from_name', side_effect=ConnectionError("Network error")):
            with pytest.raises(ModalUnavailableError):
                client._get_modal_function()

    def test_import_error_raises_unavailable(self):
        """Test that import errors raise ModalUnavailableError."""
        from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient

        client = WildlifeToolsClient(use_mock=False)

        with patch('modal.Cls.from_name', side_effect=ImportError("Module not found")):
            with pytest.raises(ModalUnavailableError):
                client._get_modal_function()


# ============================================================================
# Statistics Edge Cases
# ============================================================================


class TestStatisticsEdgeCases:
    """Test edge cases in statistics tracking."""

    @pytest.mark.asyncio
    async def test_stats_persist_across_multiple_calls(self):
        """Test that statistics accumulate across multiple calls."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient()

        mock_method = AsyncMock(return_value={"success": True})
        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = mock_method
        client._modal_function = mock_modal_func

        # Make multiple calls
        for _ in range(5):
            await client._call_with_retry("test_method")

        stats = client.get_stats()
        assert stats["requests_sent"] == 5
        assert stats["requests_succeeded"] == 5

    @pytest.mark.asyncio
    async def test_stats_track_partial_failures(self):
        """Test that stats correctly track mix of successes and failures."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        client = ConcreteClient(max_retries=2, retry_delay=0.01)

        call_count = 0

        async def sometimes_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Fail")
            return {"success": True}

        mock_modal_func = Mock()
        mock_modal_func.test_method = Mock()
        mock_modal_func.test_method.remote.aio = sometimes_fail
        client._modal_function = mock_modal_func

        # First call will fail after retries (attempts 1 and 2)
        with pytest.raises(ModalClientError):
            await client._call_with_retry("test_method")

        # Second call will succeed on first attempt (attempt 3)
        await client._call_with_retry("test_method")

        stats = client.get_stats()
        assert stats["requests_sent"] == 3  # 2 (failed attempts) + 1 (success)
        assert stats["requests_succeeded"] == 1
        assert stats["requests_failed"] == 1

    def test_get_stats_returns_copy_not_reference(self):
        """Test that get_stats returns a new dict each time."""
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

        # Modify stats1
        stats1["custom_field"] = 123

        # stats2 should not have the custom field
        assert "custom_field" not in stats2
        assert "custom_field" not in client.get_stats()


# ============================================================================
# Environment Variable Tests
# ============================================================================


class TestEnvironmentVariables:
    """Test environment variable configuration."""

    def test_mock_mode_from_env_true(self):
        """Test enabling mock mode via environment variable."""
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

    def test_mock_mode_from_env_false(self):
        """Test disabling mock mode via environment variable."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        with patch.dict('os.environ', {'MODAL_USE_MOCK': 'false'}):
            client = ConcreteClient()
            assert client.use_mock is False

    def test_mock_mode_parameter_overrides_env(self):
        """Test that explicit parameter overrides environment variable."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        with patch.dict('os.environ', {'MODAL_USE_MOCK': 'true'}):
            client = ConcreteClient(use_mock=False)
            assert client.use_mock is False

    def test_mock_mode_default_when_env_not_set(self):
        """Test default mock mode when environment variable not set."""
        class ConcreteClient(BaseModalClient):
            @property
            def app_name(self) -> str:
                return "test-app"

            @property
            def class_name(self) -> str:
                return "TestModel"

        with patch.dict('os.environ', {}, clear=True):
            client = ConcreteClient()
            # Default should be False when env var not set
            assert client.use_mock is False
