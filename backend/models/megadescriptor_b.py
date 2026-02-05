"""MegaDescriptor-B-224 model wrapper for fast tiger re-identification.

MegaDescriptor-B-224 is a faster variant of MegaDescriptor-L-384:
- Input: 224x224 (vs 384x384)
- Parameters: 88M (vs 228M)
- Speed: ~3x faster inference
- Accuracy: Slightly lower but still competitive

Use this model when speed is a priority or as a pre-filter before
running the heavier MegaDescriptor-L-384.
"""

from typing import Optional, Union, List
import io
import numpy as np
from PIL import Image

from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client
from backend.config.settings import get_settings
from backend.models.interfaces.base_reid_model import BaseReIDModel

logger = get_logger(__name__)


class MegaDescriptorBReIDModel(BaseReIDModel):
    """MegaDescriptor-B-224 ReID model using Modal backend."""

    def __init__(self):
        """Initialize MegaDescriptor-B-224 model."""
        settings = get_settings()
        self._similarity_threshold = 0.75  # Slightly lower threshold for faster model
        self.modal_client = get_modal_client()

        logger.info("MegaDescriptorBReIDModel initialized with Modal backend")

    @property
    def embedding_dim(self) -> int:
        """Get the embedding dimension for this model."""
        return 1024  # Swin-Base outputs 1024-dim

    @property
    def similarity_threshold(self) -> float:
        """Get the default similarity threshold."""
        return self._similarity_threshold

    async def load_model(self):
        """Load model (no-op for Modal backend)."""
        logger.info("Model loading handled by Modal backend")
        pass

    async def generate_embedding(self, image: Union[Image.Image, bytes]) -> np.ndarray:
        """Generate embedding for an image using Modal.

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

            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Call Modal service
            result = await self.modal_client.megadescriptor_b_embedding(image)

            if result.get("success"):
                embedding = np.array(result["embedding"])

                # Normalize
                embedding = self.normalize_embedding(embedding)

                return embedding
            else:
                error_msg = result.get("error", "Unknown error")
                raise RuntimeError(f"Modal embedding generation failed: {error_msg}")

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")

    async def generate_embedding_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Generate embedding directly from image bytes.

        Args:
            image_bytes: Image as bytes

        Returns:
            Embedding vector (numpy array)
        """
        return await self.generate_embedding(image_bytes)

    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compare two embeddings using cosine similarity.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            if embedding1.ndim > 1:
                embedding1 = embedding1.flatten()
            if embedding2.ndim > 1:
                embedding2 = embedding2.flatten()

            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )

            return float(similarity)

        except Exception as e:
            logger.error(f"Failed to compare embeddings: {e}")
            return 0.0

    def identify(
        self,
        query_embedding: np.ndarray,
        database_embeddings: List[np.ndarray],
        database_labels: List[str],
        k: int = 1
    ) -> tuple:
        """Identify a query embedding against a database using k-NN.

        Args:
            query_embedding: Query embedding vector
            database_embeddings: List of database embedding vectors
            database_labels: List of labels corresponding to database embeddings
            k: Number of nearest neighbors to consider

        Returns:
            Tuple of (predicted_label, similarity_score)
        """
        try:
            similarities = []
            for db_embedding in database_embeddings:
                sim = self.compare_embeddings(query_embedding, db_embedding)
                similarities.append(sim)

            similarities_array = np.array(similarities)
            top_k_indices = np.argsort(similarities_array)[-k:][::-1]

            best_idx = top_k_indices[0]
            predicted_label = database_labels[best_idx]
            similarity_score = similarities_array[best_idx]

            return str(predicted_label), float(similarity_score)

        except Exception as e:
            logger.error(f"Failed to identify: {e}")
            return None, 0.0
