"""OmniVinci Modal client."""

from typing import Dict, Any, Optional, List
from pathlib import Path

from backend.infrastructure.modal.base_client import (
    BaseModalClient,
    ModalUnavailableError,
    ModalClientError,
)
from backend.infrastructure.modal.mock_provider import MockResponseProvider
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class OmniVinciClient(BaseModalClient):
    """Client for OmniVinci model on Modal."""

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "OmniVinciModel"

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str = "Analyze this image in detail and describe what you see."
    ) -> Dict[str, Any]:
        """Analyze an image using OmniVinci.

        Args:
            image_bytes: Image as bytes
            prompt: Analysis prompt

        Returns:
            Dictionary with detailed visual analysis
        """
        if self.use_mock:
            return MockResponseProvider.omnivinci_image_analysis()

        try:
            result = await self._call_with_retry(
                "analyze_image",
                image_bytes,
                prompt
            )

            if result.get("success"):
                logger.info(
                    f"OmniVinci analysis completed: "
                    f"{len(result.get('analysis', ''))} chars"
                )
            else:
                logger.error(f"OmniVinci analysis failed: {result.get('error')}")

            return result

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for OmniVinci image: {e}")
            return {
                "success": False,
                "error": "OmniVinci service unavailable",
                "analysis": None
            }

    async def analyze_video(
        self,
        video_path: Path,
        prompt: str = "Analyze this video and describe what you see.",
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a video using OmniVinci.

        Args:
            video_path: Path to video file
            prompt: Analysis prompt
            tools: Optional list of tools
            tool_callback_url: URL for tool callbacks

        Returns:
            Dictionary with analysis results
        """
        if self.use_mock:
            return MockResponseProvider.omnivinci_video_analysis()

        try:
            # Load video bytes
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            return await self._call_with_retry(
                "analyze_video",
                video_bytes,
                prompt,
                tools,
                tool_callback_url
            )

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal failed for OmniVinci video: {e}")
            return {
                "success": False,
                "error": "OmniVinci service unavailable",
                "analysis": None
            }


# Singleton instance
_client = None


def get_omnivinci_client() -> OmniVinciClient:
    """Get singleton OmniVinci client instance."""
    global _client
    if _client is None:
        _client = OmniVinciClient()
    return _client
