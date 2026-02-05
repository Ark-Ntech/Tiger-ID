"""MatchAnything Modal client."""

from typing import Dict, Any
import io
from PIL import Image

from backend.infrastructure.modal.base_client import (
    BaseModalClient,
    ModalUnavailableError,
    ModalClientError,
)
from backend.infrastructure.modal.clients.base_client import create_singleton_getter
from backend.infrastructure.modal.mock_provider import MockResponseProvider
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class MatchAnythingClient(BaseModalClient):
    """Client for MatchAnything model on Modal.

    MatchAnything-ELOFTR is a keypoint matching model that finds
    corresponding points between image pairs. Unlike ReID models that
    generate embeddings, this model compares images directly.

    Used for verification of tiger identity by matching stripe patterns.

    Note: This client does NOT extend EmbeddingModalClient because it
    performs image matching rather than embedding generation.
    """

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "MatchAnythingModel"

    def _image_to_bytes(self, image: Image.Image, format: str = 'JPEG') -> bytes:
        """Convert PIL Image to bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    async def match_images(
        self,
        image1: Image.Image,
        image2: Image.Image,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """Match two images and return keypoint correspondences.

        Args:
            image1: First PIL Image (query)
            image2: Second PIL Image (candidate)
            threshold: Confidence threshold for keypoint filtering

        Returns:
            Dictionary with matching results:
            - num_matches: Number of keypoint correspondences
            - mean_score: Average confidence of matches
            - max_score: Maximum match confidence
            - total_score: Sum of all match confidences
            - success: Whether matching succeeded
        """
        if self.use_mock:
            return MockResponseProvider.matchanything_match()

        try:
            image1_bytes = self._image_to_bytes(image1)
            image2_bytes = self._image_to_bytes(image2)

            return await self._call_with_retry(
                "match_images",
                image1_bytes,
                image2_bytes,
                threshold
            )

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for MatchAnything: {e}")
            logger.warning("Falling back to mock response")
            return MockResponseProvider.matchanything_match()

    async def match_images_bytes(
        self,
        image1_bytes: bytes,
        image2_bytes: bytes,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """Match two images from bytes.

        Args:
            image1_bytes: First image as bytes
            image2_bytes: Second image as bytes
            threshold: Confidence threshold

        Returns:
            Dictionary with matching results
        """
        if self.use_mock:
            return MockResponseProvider.matchanything_match()

        try:
            return await self._call_with_retry(
                "match_images",
                image1_bytes,
                image2_bytes,
                threshold
            )

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for MatchAnything: {e}")
            return MockResponseProvider.matchanything_match()

    async def health_check(self) -> Dict[str, Any]:
        """Check if the model is healthy."""
        if self.use_mock:
            return {"status": "mock", "model_name": "MatchAnything"}

        try:
            return await self._call_with_retry("health_check")
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Singleton getter
get_matchanything_client = create_singleton_getter(MatchAnythingClient, "MatchAnything")
