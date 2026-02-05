"""Base class for embedding-generating Modal clients.

This module provides a specialized base class for Modal clients that generate
embeddings from images. It builds on the core BaseModalClient and adds:
- Common image-to-bytes conversion
- Mock response handling with fallback
- Generic singleton factory pattern
"""

from abc import abstractmethod
from typing import Dict, Any, Optional, Callable, TypeVar, Type
import io
from PIL import Image

from backend.infrastructure.modal.base_client import (
    BaseModalClient as CoreModalClient,
    ModalUnavailableError,
    ModalClientError,
)
from backend.infrastructure.modal.mock_provider import MockResponseProvider
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Type variable for singleton factory
T = TypeVar('T', bound='EmbeddingModalClient')


class EmbeddingModalClient(CoreModalClient):
    """Base class for Modal clients that generate image embeddings.

    This class provides common functionality for ReID model clients:
    - Image to bytes conversion
    - Mock mode handling with automatic fallback
    - Standard generate_embedding interface

    Subclasses must implement:
    - app_name: Modal app name
    - class_name: Modal class name
    - EMBEDDING_DIM: Output embedding dimension
    - _get_mock_response(): Return mock response for this model

    Example usage:
        class MyModelClient(EmbeddingModalClient):
            EMBEDDING_DIM = 1024

            @property
            def app_name(self) -> str:
                return "tiger-id-models"

            @property
            def class_name(self) -> str:
                return "MyModel"

            def _get_mock_response(self) -> Dict[str, Any]:
                return MockResponseProvider.get_embedding_response(
                    "my_model", self.EMBEDDING_DIM
                )
    """

    # Subclasses must override this
    EMBEDDING_DIM: int = NotImplemented

    @abstractmethod
    def _get_mock_response(self) -> Dict[str, Any]:
        """Return mock response for this model.

        Subclasses should call the appropriate MockResponseProvider method.

        Returns:
            Mock embedding response dictionary
        """
        pass

    @property
    def model_name(self) -> str:
        """Human-readable model name for logging.

        Defaults to class_name, but can be overridden.
        """
        return self.class_name

    def _image_to_bytes(self, image: Image.Image, format: str = 'JPEG') -> bytes:
        """Convert PIL Image to bytes.

        Args:
            image: PIL Image to convert
            format: Image format (default: JPEG)

        Returns:
            Image as bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    async def generate_embedding(self, image: Image.Image) -> Dict[str, Any]:
        """Generate embedding for an image.

        Handles:
        - Mock mode (returns mock response immediately)
        - Image to bytes conversion
        - Modal call with retry
        - Fallback to mock on error

        Args:
            image: PIL Image to generate embedding for

        Returns:
            Dictionary with embedding vector and metadata:
            - success: bool
            - embedding: List[float] of length EMBEDDING_DIM
            - shape: Tuple of embedding dimensions
            - mock: bool (True if mock response)
        """
        if self.use_mock:
            return self._get_mock_response()

        try:
            image_bytes = self._image_to_bytes(image)

            return await self._call_with_retry(
                "generate_embedding",
                image_bytes
            )

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for {self.model_name}: {e}")
            logger.warning("Falling back to mock response")
            return self._get_mock_response()

    async def generate_embedding_from_bytes(
        self,
        image_bytes: bytes
    ) -> Dict[str, Any]:
        """Generate embedding from image bytes directly.

        Useful when image is already in bytes format.

        Args:
            image_bytes: Image as bytes

        Returns:
            Dictionary with embedding vector and metadata
        """
        if self.use_mock:
            return self._get_mock_response()

        try:
            return await self._call_with_retry(
                "generate_embedding",
                image_bytes
            )

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for {self.model_name}: {e}")
            logger.warning("Falling back to mock response")
            return self._get_mock_response()


def create_singleton_getter(
    client_class: Type[T],
    client_name: str
) -> Callable[[], T]:
    """Create a singleton getter function for a Modal client.

    Args:
        client_class: The client class to instantiate
        client_name: Name for logging purposes

    Returns:
        Function that returns singleton instance

    Example:
        get_my_client = create_singleton_getter(MyClient, "MyClient")
        client = get_my_client()  # Returns singleton instance
    """
    _instance: Optional[T] = None

    def get_client() -> T:
        nonlocal _instance
        if _instance is None:
            _instance = client_class()
        return _instance

    get_client.__doc__ = f"Get singleton {client_name} instance."
    return get_client
