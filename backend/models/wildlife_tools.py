"""WildlifeTools integration for tiger re-identification using Modal

WildlifeTools provides training and inference tooling for wildlife Re-ID models
including MegaDescriptor and WildFusion models.
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


class WildlifeToolsReIDModel(BaseReIDModel):
    """Wrapper for WildlifeTools Re-ID models (MegaDescriptor/WildFusion) using Modal"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        model_type: str = "megadescriptor",
        device: Optional[str] = None,
        batch_size: int = 128
    ):
        """
        Initialize WildlifeTools Re-ID model (Modal-based).

        Args:
            model_name: HuggingFace model name (deprecated, kept for compatibility)
            model_type: Model type (deprecated, kept for compatibility)
            device: Device to run model on (deprecated, kept for compatibility)
            batch_size: Batch size for feature extraction (deprecated, kept for compatibility)
        """
        self._model_name = model_name
        self.model_type = model_type
        self.batch_size = batch_size
        settings = get_settings()
        self._similarity_threshold = settings.models.wildlife_tools.similarity_threshold
        self.modal_client = get_modal_client()

        logger.info("WildlifeToolsReIDModel initialized with Modal backend")

    @property
    def embedding_dim(self) -> int:
        """Get the embedding dimension for this model."""
        return 1536

    @property
    def similarity_threshold(self) -> float:
        """Get the default similarity threshold."""
        return self._similarity_threshold
        
    async def load_model(self):
        """
        Load the WildlifeTools model (no-op for Modal backend).
        
        Model is loaded on Modal containers automatically.
        """
        logger.info("Model loading handled by Modal backend")
        pass
    
    async def generate_embedding(self, image: Union[Image.Image, bytes]) -> np.ndarray:
        """
        Generate embedding for an image using Modal.

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
            result = await self.modal_client.wildlife_tools_embedding(image)

            if result.get("success"):
                embedding = np.array(result["embedding"])

                # Normalize
                embedding = self.normalize_embedding(embedding)

                return embedding
            else:
                error_msg = result.get("error", "Unknown error")

                # Check if request was queued
                if result.get("queued"):
                    logger.warning("WildlifeTools embedding request queued for later processing")
                    raise RuntimeError("Request queued, embedding not immediately available")

                raise RuntimeError(f"Modal embedding generation failed: {error_msg}")

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
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
    
    def identify(self, query_embedding: np.ndarray, database_embeddings: List[np.ndarray], database_labels: List[str], k: int = 1) -> tuple:
        """
        Identify a query embedding against a database using k-NN.
        
        Args:
            query_embedding: Query embedding vector
            database_embeddings: List of database embedding vectors
            database_labels: List of labels corresponding to database embeddings
            k: Number of nearest neighbors to consider
            
        Returns:
            Tuple of (predicted_label, similarity_score)
        """
        try:
            # Compute similarities with all database embeddings
            similarities = []
            for db_embedding in database_embeddings:
                sim = self.compare_embeddings(query_embedding, db_embedding)
                similarities.append(sim)
            
            # Get top-k matches
            similarities_array = np.array(similarities)
            top_k_indices = np.argsort(similarities_array)[-k:][::-1]
            
            # Return best match
            best_idx = top_k_indices[0]
            predicted_label = database_labels[best_idx]
            similarity_score = similarities_array[best_idx]
            
            return str(predicted_label), float(similarity_score)
            
        except Exception as e:
            logger.error(f"Failed to identify: {e}")
            return None, 0.0

