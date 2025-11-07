"""Siamese network for tiger stripe re-identification using Modal"""

import os
from PIL import Image
import numpy as np
from typing import Optional, List, Tuple
import io

from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client
from backend.config.settings import get_settings

logger = get_logger(__name__)


class TigerReIDModel:
    """Tiger stripe re-identification model using Modal"""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize tiger re-ID model (Modal-based).
        
        Args:
            model_path: Path to model checkpoint (deprecated, kept for compatibility)
            device: Device to run model on (deprecated, kept for compatibility)
        """
        settings = get_settings()
        self.model_path = model_path or settings.models.reid_path
        self.embedding_dim = settings.models.reid_embedding_dim
        self.modal_client = get_modal_client()
        
        logger.info("TigerReIDModel initialized with Modal backend")
    
    async def load_model(self):
        """
        Load the re-ID model (no-op for Modal backend).
        
        Model is loaded on Modal containers automatically.
        """
        logger.info("Model loading handled by Modal backend")
        pass
    
    async def generate_embedding(
        self,
        image: Image.Image,
        use_flip: bool = False
    ) -> np.ndarray:
        """
        Generate embedding for a tiger image using Modal.
        
        Args:
            image: PIL Image of tiger
            use_flip: Whether to also use horizontally flipped version (not supported in Modal yet)
            
        Returns:
            Embedding vector (numpy array)
        """
        try:
            # Call Modal service
            result = await self.modal_client.tiger_reid_embedding(image)
            
            if result.get("success"):
                embedding = np.array(result["embedding"])
                
                # Normalize
                embedding = embedding / np.linalg.norm(embedding)
                
                return embedding
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Modal embedding generation failed: {error_msg}")
                raise RuntimeError(f"Failed to generate embedding: {error_msg}")
            
        except Exception as e:
            logger.error("Error generating embedding", error=str(e))
            raise
    
    async def generate_embedding_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Generate embedding from image bytes"""
        image = Image.open(io.BytesIO(image_bytes))
        return await self.generate_embedding(image)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(similarity)

