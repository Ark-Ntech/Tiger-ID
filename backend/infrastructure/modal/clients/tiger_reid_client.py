"""Tiger ReID Modal client."""

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


class TigerReIDClient(BaseModalClient):
    """Client for Tiger ReID model on Modal."""

    EMBEDDING_DIM = 2048

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "TigerReIDModel"

    async def generate_embedding(self, image: Image.Image) -> Dict[str, Any]:
        """Generate tiger ReID embedding.

        Args:
            image: PIL Image

        Returns:
            Dictionary with embedding vector
        """
        if self.use_mock:
            return MockResponseProvider.tiger_reid_embedding(self.EMBEDDING_DIM)

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
            logger.error(f"Modal failed for TigerReID: {e}")
            logger.warning("Falling back to mock response")
            return MockResponseProvider.tiger_reid_embedding(self.EMBEDDING_DIM)


# Singleton instance
_client = None


def get_tiger_reid_client() -> TigerReIDClient:
    """Get singleton TigerReID client instance."""
    global _client
    if _client is None:
        _client = TigerReIDClient()
    return _client
