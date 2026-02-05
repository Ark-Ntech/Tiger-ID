"""Pytest configuration and fixtures for Modal client tests."""

import pytest
from PIL import Image
import numpy as np


@pytest.fixture
def sample_rgb_image():
    """Create a sample RGB image for testing.

    Returns:
        PIL.Image: A 100x100 RGB image with random pixel values
    """
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    return Image.fromarray(img_array)


@pytest.fixture
def sample_image_pair():
    """Create a pair of sample images for matching tests.

    Returns:
        tuple: Two PIL Images with different sizes
    """
    img1 = Image.fromarray(np.random.randint(0, 255, (200, 150, 3), dtype=np.uint8))
    img2 = Image.fromarray(np.random.randint(0, 255, (150, 200, 3), dtype=np.uint8))
    return img1, img2


@pytest.fixture
def sample_large_image():
    """Create a large sample image for performance testing.

    Returns:
        PIL.Image: A 1000x1000 RGB image
    """
    img_array = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)
    return Image.fromarray(img_array)


@pytest.fixture
def sample_grayscale_image():
    """Create a grayscale image for format testing.

    Returns:
        PIL.Image: A 100x100 grayscale image
    """
    img_array = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    return Image.fromarray(img_array)


@pytest.fixture
def sample_rgba_image():
    """Create an RGBA image with transparency for format testing.

    Returns:
        PIL.Image: A 100x100 RGBA image
    """
    img_array = np.random.randint(0, 255, (100, 100, 4), dtype=np.uint8)
    return Image.fromarray(img_array)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to ensure isolation.

    This fixture runs automatically before each test to prevent
    singleton state from leaking between tests.
    """
    # Import all client modules
    from backend.infrastructure.modal.clients import wildlife_tools_client
    from backend.infrastructure.modal.clients import cvwc2019_client
    from backend.infrastructure.modal.clients import transreid_client
    from backend.infrastructure.modal.clients import megadescriptor_b_client
    from backend.infrastructure.modal.clients import matchanything_client

    # Reset singleton instances
    wildlife_tools_client._client = None
    cvwc2019_client._client = None
    transreid_client._client = None
    megadescriptor_b_client._client = None
    matchanything_client._client = None

    yield

    # Clean up after test
    wildlife_tools_client._client = None
    cvwc2019_client._client = None
    transreid_client._client = None
    megadescriptor_b_client._client = None
    matchanything_client._client = None


@pytest.fixture
def mock_modal_response():
    """Factory fixture for creating mock Modal responses.

    Returns:
        function: A factory function that creates mock responses
    """
    def _create_response(embedding_dim=2048, success=True, mock=True):
        """Create a mock embedding response.

        Args:
            embedding_dim: Dimension of embedding vector
            success: Whether the response indicates success
            mock: Whether to mark as mock response

        Returns:
            dict: Mock response dictionary
        """
        return {
            "success": success,
            "embedding": [0.0] * embedding_dim if success else None,
            "shape": (embedding_dim,) if success else None,
            "mock": mock
        }

    return _create_response


@pytest.fixture
def mock_match_response():
    """Factory fixture for creating mock matching responses.

    Returns:
        function: A factory function that creates mock match responses
    """
    def _create_response(num_matches=100, success=True, mock=True):
        """Create a mock matching response.

        Args:
            num_matches: Number of keypoint matches
            success: Whether the response indicates success
            mock: Whether to mark as mock response

        Returns:
            dict: Mock match response dictionary
        """
        if not success:
            return {"success": False, "error": "Matching failed", "mock": mock}

        scores = np.random.uniform(0.3, 0.9, num_matches)

        return {
            "success": True,
            "num_matches": num_matches,
            "mean_score": float(scores.mean()) if num_matches > 0 else 0.0,
            "max_score": float(scores.max()) if num_matches > 0 else 0.0,
            "min_score": float(scores.min()) if num_matches > 0 else 0.0,
            "total_score": float(scores.sum()) if num_matches > 0 else 0.0,
            "mock": mock
        }

    return _create_response


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "requires_modal: marks tests that require Modal connection"
    )
