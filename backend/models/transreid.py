"""
TransReID Model Wrapper for Tiger ID.

TransReID is a Vision Transformer-based re-identification model that uses:
- Side Information Embeddings (SIE) to encode viewpoint/camera information
- Jigsaw Patch Module (JPM) to capture local patterns
- Pure ViT architecture for global feature learning

Reference:
- Paper: TransReID: Transformer-based Object Re-Identification (ICCV 2021)
- GitHub: https://github.com/damo-cv/TransReID

This wrapper uses Modal for serverless GPU inference with pretrained weights.
"""

from typing import Dict, Any, Optional, List
import numpy as np
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class TransReIDModel:
    """
    TransReID model wrapper for tiger re-identification.

    Uses Vision Transformer (ViT) architecture with pretrained weights
    for robust feature extraction. Can be used standalone or as part
    of an ensemble with CNN-based models.
    """

    def __init__(
        self,
        model_variant: str = "vit_base",
        use_sie: bool = True,
        use_jpm: bool = True
    ):
        """
        Initialize TransReID model.

        Args:
            model_variant: Model variant ('vit_base', 'deit_base', 'vit_small')
            use_sie: Whether to use Side Information Embeddings
            use_jpm: Whether to use Jigsaw Patch Module
        """
        self.model_variant = model_variant
        self.use_sie = use_sie
        self.use_jpm = use_jpm
        self.settings = get_settings()
        self._model_cls = None

        # Embedding dimension depends on variant
        self.embedding_dim = 768 if 'base' in model_variant else 384
        logger.info(f"Initialized TransReID wrapper ({model_variant})")

    def _get_modal_model(self):
        """Get Modal model class for remote inference."""
        if self._model_cls is None:
            import modal
            try:
                self._model_cls = modal.Cls.from_name(
                    "tiger-id-models",
                    "TransReIDModel"
                )
                logger.info("Connected to Modal TransReID model")
            except Exception as e:
                logger.error(f"Failed to connect to Modal: {e}")
                raise
        return self._model_cls

    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Generate embedding for a tiger image.

        Args:
            image_bytes: Image as bytes

        Returns:
            Dictionary with embedding vector and metadata
        """
        try:
            model = self._get_modal_model()
            result = model().generate_embedding.remote(image_bytes)
            return result
        except Exception as e:
            logger.error(f"TransReID embedding generation failed: {e}")
            return {
                "embedding": None,
                "error": str(e),
                "success": False
            }

    def generate_embedding_batch(
        self,
        images: List[bytes]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of images.

        Args:
            images: List of images as bytes

        Returns:
            List of embedding results
        """
        try:
            model = self._get_modal_model()
            results = model().generate_embedding_batch.remote(images)
            return results
        except Exception as e:
            logger.error(f"TransReID batch embedding failed: {e}")
            return [{"embedding": None, "error": str(e), "success": False}] * len(images)

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        gallery_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and gallery embeddings.

        Args:
            query_embedding: Query embedding vector
            gallery_embeddings: Gallery embedding matrix

        Returns:
            Similarity scores for each gallery item
        """
        # Ensure embeddings are normalized
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        gallery_norms = gallery_embeddings / (
            np.linalg.norm(gallery_embeddings, axis=1, keepdims=True) + 1e-8
        )

        # Cosine similarity
        similarities = np.dot(gallery_norms, query_norm)
        return similarities

    def get_model_info(self) -> Dict[str, Any]:
        """Get model configuration information."""
        return {
            "name": "TransReID",
            "variant": self.model_variant,
            "embedding_dim": self.embedding_dim,
            "use_sie": self.use_sie,
            "use_jpm": self.use_jpm,
            "architecture": "Vision Transformer",
            "pretrained": "ImageNet-21K"
        }


def create_transreid_model(
    variant: str = "vit_base",
    use_sie: bool = True,
    use_jpm: bool = True
) -> TransReIDModel:
    """
    Factory function to create a TransReID model.

    Args:
        variant: Model variant
        use_sie: Use Side Information Embeddings
        use_jpm: Use Jigsaw Patch Module

    Returns:
        TransReIDModel instance
    """
    return TransReIDModel(
        model_variant=variant,
        use_sie=use_sie,
        use_jpm=use_jpm
    )
