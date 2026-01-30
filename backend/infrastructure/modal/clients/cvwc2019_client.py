"""CVWC2019 ReID Modal client."""

from typing import Dict, Any
import io
from PIL import Image

from backend.infrastructure.modal.base_client import (
    BaseModalClient,
    ModalUnavailableError,
    ModalClientError,
)
from backend.infrastructure.modal.mock_provider import MockResponseProvider
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class CVWC2019Client(BaseModalClient):
    """Client for CVWC2019 ReID model on Modal."""

    EMBEDDING_DIM = 3072

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "CVWC2019ReIDModel"

    async def generate_embedding(self, image: Image.Image) -> Dict[str, Any]:
        """Generate CVWC2019 embedding.

        Args:
            image: PIL Image

        Returns:
            Dictionary with embedding vector
        """
        if self.use_mock:
            return MockResponseProvider.cvwc2019_embedding(self.EMBEDDING_DIM)

        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()

            return await self._call_with_retry(
                "generate_embedding",
                image_bytes
            )

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for CVWC2019: {e}")
            logger.warning("Falling back to mock response")
            return MockResponseProvider.cvwc2019_embedding(self.EMBEDDING_DIM)


# Singleton instance
_client = None


def get_cvwc2019_client() -> CVWC2019Client:
    """Get singleton CVWC2019 client instance."""
    global _client
    if _client is None:
        _client = CVWC2019Client()
    return _client
