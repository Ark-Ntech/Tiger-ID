"""Mock response provider for development and testing."""

from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class MockResponseProvider:
    """Provides mock responses for Modal services during development.

    Used when Modal is unavailable or mock mode is enabled,
    allowing development and testing without real Modal infrastructure.
    """

    @staticmethod
    def tiger_reid_embedding(embedding_dim: int = 2048) -> Dict[str, Any]:
        """Generate mock tiger ReID embedding.

        Args:
            embedding_dim: Dimension of embedding vector

        Returns:
            Mock embedding response
        """
        logger.info(f"[MOCK] Generating TigerReID embedding ({embedding_dim}d)")
        return {
            "success": True,
            "embedding": np.random.rand(embedding_dim).tolist(),
            "shape": (embedding_dim,),
            "mock": True
        }

    @staticmethod
    def wildlife_tools_embedding(embedding_dim: int = 2048) -> Dict[str, Any]:
        """Generate mock WildlifeTools embedding.

        Args:
            embedding_dim: Dimension of embedding vector

        Returns:
            Mock embedding response
        """
        logger.info(f"[MOCK] Generating WildlifeTools embedding ({embedding_dim}d)")
        return {
            "success": True,
            "embedding": np.random.rand(embedding_dim).tolist(),
            "shape": (embedding_dim,),
            "mock": True
        }

    @staticmethod
    def rapid_reid_embedding(embedding_dim: int = 2048) -> Dict[str, Any]:
        """Generate mock RAPID embedding.

        Args:
            embedding_dim: Dimension of embedding vector

        Returns:
            Mock embedding response
        """
        logger.info(f"[MOCK] Generating RAPID embedding ({embedding_dim}d)")
        return {
            "success": True,
            "embedding": np.random.rand(embedding_dim).tolist(),
            "shape": (embedding_dim,),
            "mock": True
        }

    @staticmethod
    def cvwc2019_embedding(embedding_dim: int = 3072) -> Dict[str, Any]:
        """Generate mock CVWC2019 embedding.

        Args:
            embedding_dim: Dimension of embedding vector

        Returns:
            Mock embedding response
        """
        logger.info(f"[MOCK] Generating CVWC2019 embedding ({embedding_dim}d)")
        return {
            "success": True,
            "embedding": np.random.rand(embedding_dim).tolist(),
            "shape": (embedding_dim,),
            "mock": True
        }

    @staticmethod
    def megadetector_detection(image_size: Tuple[int, int]) -> Dict[str, Any]:
        """Generate mock MegaDetector detection response.

        Args:
            image_size: Tuple of (width, height) of the image

        Returns:
            Mock detection response with a single animal detection
        """
        w, h = image_size
        logger.info(f"[MOCK] Generating MegaDetector detection ({w}x{h})")

        # Generate a realistic-looking bounding box
        # Center the detection with some padding
        padding = 0.1
        return {
            "success": True,
            "detections": [
                {
                    "bbox": [
                        int(w * padding),
                        int(h * padding),
                        int(w * (1 - padding)),
                        int(h * (1 - padding))
                    ],
                    "confidence": 0.95,
                    "category": "animal",
                    "class_id": 0
                }
            ],
            "mock": True
        }

    @staticmethod
    def omnivinci_image_analysis() -> Dict[str, Any]:
        """Generate mock OmniVinci image analysis.

        Returns:
            Mock visual analysis response
        """
        logger.info("[MOCK] Generating OmniVinci image analysis")
        return {
            "success": True,
            "analysis": (
                "Mock visual analysis: Tiger appears to be an adult "
                "Amur tiger in a natural setting. Stripe patterns are "
                "clearly visible along the flanks. The tiger's posture "
                "suggests alertness. Image quality is suitable for "
                "identification purposes."
            ),
            "mock": True
        }

    @staticmethod
    def omnivinci_video_analysis() -> Dict[str, Any]:
        """Generate mock OmniVinci video analysis.

        Returns:
            Mock video analysis response
        """
        logger.info("[MOCK] Generating OmniVinci video analysis")
        return {
            "success": True,
            "analysis": (
                "Mock video analysis: Video shows a tiger moving through "
                "dense vegetation. Multiple stripe patterns captured from "
                "different angles. Behavior appears natural and undisturbed."
            ),
            "frames_analyzed": 30,
            "mock": True
        }

    @classmethod
    def get_embedding_response(
        cls,
        model_name: str,
        embedding_dim: int = None
    ) -> Dict[str, Any]:
        """Get mock embedding response for any ReID model.

        Args:
            model_name: Name of the model
            embedding_dim: Optional embedding dimension override

        Returns:
            Mock embedding response
        """
        # Default dimensions per model
        default_dims = {
            "tiger_reid": 2048,
            "wildlife_tools": 2048,
            "rapid_reid": 2048,
            "cvwc2019_reid": 3072,
        }

        dim = embedding_dim or default_dims.get(model_name, 2048)

        logger.info(f"[MOCK] Generating {model_name} embedding ({dim}d)")
        return {
            "success": True,
            "embedding": np.random.rand(dim).tolist(),
            "shape": (dim,),
            "model": model_name,
            "mock": True
        }

    @classmethod
    def get_detection_response(
        cls,
        image: Image.Image
    ) -> Dict[str, Any]:
        """Get mock detection response for an image.

        Args:
            image: PIL Image

        Returns:
            Mock detection response
        """
        return cls.megadetector_detection(image.size)
