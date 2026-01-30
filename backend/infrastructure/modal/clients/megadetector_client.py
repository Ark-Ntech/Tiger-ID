"""MegaDetector Modal client."""

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


class MegaDetectorClient(BaseModalClient):
    """Client for MegaDetector model on Modal."""

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "MegaDetectorModel"

    async def detect(
        self,
        image: Image.Image,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Detect animals in an image.

        Args:
            image: PIL Image
            confidence_threshold: Detection confidence threshold

        Returns:
            Dictionary with detection results
        """
        if self.use_mock:
            return MockResponseProvider.megadetector_detection(image.size)

        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()

            return await self._call_with_retry(
                "detect",
                image_bytes,
                confidence_threshold
            )

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for MegaDetector: {e}")
            logger.warning("Falling back to mock response")
            return MockResponseProvider.megadetector_detection(image.size)


# Singleton instance
_client = None


def get_megadetector_client() -> MegaDetectorClient:
    """Get singleton MegaDetector client instance."""
    global _client
    if _client is None:
        _client = MegaDetectorClient()
    return _client
