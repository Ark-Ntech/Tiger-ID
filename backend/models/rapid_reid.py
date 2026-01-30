"""RAPID (Real-time Animal Pattern re-ID) integration using Modal

RAPID is a real-time animal pattern re-identification model for edge devices.
Paper: https://www.biorxiv.org/content/10.1101/2025.07.07.663143.full.pdf
"""

from typing import Optional, Dict, Any, List, Union
import io
from PIL import Image
import numpy as np

from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client
from backend.config.settings import get_settings
from backend.models.interfaces.base_reid_model import BaseReIDModel

logger = get_logger(__name__)


class RAPIDReIDModel(BaseReIDModel):
    """Wrapper for RAPID real-time animal pattern re-ID model using Modal"""

    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize RAPID Re-ID model (Modal-based).

        Args:
            model_path: Path to model checkpoint (deprecated, kept for compatibility)
            device: Device to run model on (deprecated, kept for compatibility)
        """
        settings = get_settings()
        self.model_path = model_path or settings.models.rapid.path
        self._similarity_threshold = settings.models.rapid.similarity_threshold
        self.modal_client = get_modal_client()

        logger.info("RAPIDReIDModel initialized with Modal backend")

    @property
    def embedding_dim(self) -> int:
        """Get the embedding dimension for this model."""
        return 2048

    @property
    def similarity_threshold(self) -> float:
        """Get the default similarity threshold."""
        return self._similarity_threshold
        
    async def load_model(self):
        """
        Load the RAPID model (no-op for Modal backend).
        
        Model is loaded on Modal containers automatically.
        """
        logger.info("Model loading handled by Modal backend")
        pass
    
    async def generate_embedding(self, image: Union[Image.Image, bytes]) -> np.ndarray:
        """
        Generate embedding for an image using RAPID via Modal.

        Args:
            image: PIL Image or image bytes

        Returns:
            Embedding vector (numpy array)

        Raises:
            RuntimeError: If embedding generation fails
        """
        try:
            # Handle bytes input
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))

            # Call Modal service
            result = await self.modal_client.rapid_reid_embedding(image)

            if result.get("success"):
                embedding = np.array(result["embedding"])

                # Normalize
                embedding = self.normalize_embedding(embedding)

                return embedding
            else:
                error_msg = result.get("error", "Unknown error")

                # Check if request was queued
                if result.get("queued"):
                    logger.warning("RAPID embedding request queued for later processing")
                    raise RuntimeError("Request queued, embedding not immediately available")

                raise RuntimeError(f"Modal embedding generation failed: {error_msg}")

        except Exception as e:
            logger.error(f"Error generating RAPID embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two embeddings and return similarity score using cosine similarity.
        
        Args:
            embedding1: First embedding vector (numpy array)
            embedding2: Second embedding vector (numpy array)
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to compare embeddings: {e}")
            return 0.0

