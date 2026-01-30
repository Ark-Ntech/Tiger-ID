"""CVWC2019 Amur Tiger Re-ID integration using Modal

Part-pose guided approach for tiger re-identification from CVWC 2019 workshop.
Paper: https://openaccess.thecvf.com/content_ICCVW_2019/papers/CVWC/Liu_Part-Pose_Guided_Amur_Tiger_Re-Identification_ICCVW_2019_paper.pdf
"""

from typing import Optional, Dict, Any, List, Union
import io
import numpy as np
from PIL import Image

from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client
from backend.config.settings import get_settings
from backend.models.interfaces.base_reid_model import BaseReIDModel

logger = get_logger(__name__)


class CVWC2019ReIDModel(BaseReIDModel):
    """Wrapper for CVWC2019 part-pose guided tiger Re-ID model using Modal"""

    def __init__(
        self,
        model_path: Optional[str] = None,
        config_file: Optional[str] = None,
        device: Optional[str] = None,
        num_classes: int = 92  # Default ATRW has 92 tigers
    ):
        """
        Initialize CVWC2019 Re-ID model (Modal-based).

        Args:
            model_path: Path to model checkpoint (deprecated, kept for compatibility)
            config_file: Path to YAML config file (deprecated, kept for compatibility)
            device: Device to run model on (deprecated, kept for compatibility)
            num_classes: Number of classes (deprecated, kept for compatibility)
        """
        settings = get_settings()
        self.model_path = model_path or settings.models.cvwc2019.path
        self.config_file = config_file
        self.num_classes = num_classes
        self._similarity_threshold = settings.models.cvwc2019.similarity_threshold
        self.modal_client = get_modal_client()

        logger.info("CVWC2019ReIDModel initialized with Modal backend")

    @property
    def embedding_dim(self) -> int:
        """Get the embedding dimension for this model."""
        return 3072  # CVWC2019 uses 3072-dimensional embeddings

    @property
    def similarity_threshold(self) -> float:
        """Get the default similarity threshold."""
        return self._similarity_threshold
        
    async def load_model(self):
        """
        Load the CVWC2019 model (no-op for Modal backend).
        
        Model is loaded on Modal containers automatically.
        """
        logger.info("Model loading handled by Modal backend")
        pass
    
    async def generate_embedding(self, image: Union[Image.Image, bytes]) -> np.ndarray:
        """
        Generate embedding for an image using part-pose guided approach via Modal.

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
            result = await self.modal_client.cvwc2019_reid_embedding(image)

            if result.get("success"):
                embedding = np.array(result["embedding"])

                # Normalize
                embedding = self.normalize_embedding(embedding)

                return embedding
            else:
                error_msg = result.get("error", "Unknown error")

                # Check if request was queued
                if result.get("queued"):
                    logger.warning("CVWC2019 embedding request queued for later processing")
                    raise RuntimeError("Request queued, embedding not immediately available")

                raise RuntimeError(f"Modal embedding generation failed: {error_msg}")

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    async def generate_embedding_from_bytes(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        Generate embedding from image bytes (alias for generate_embedding for compatibility).
        
        Args:
            image_data: Image bytes
            
        Returns:
            Embedding vector (numpy array) or None if failed
        """
        return await self.generate_embedding(image_data)
    
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
            # Ensure embeddings are 1D
            if embedding1.ndim > 1:
                embedding1 = embedding1.flatten()
            if embedding2.ndim > 1:
                embedding2 = embedding2.flatten()
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compare embeddings: {e}")
            return 0.0

