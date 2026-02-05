"""Service layer for image embedding operations.

Provides functionality for:
- Storing and retrieving embeddings
- Multi-view embedding fusion
- Quality-based embedding filtering
- Similarity search
"""

from typing import Optional, List, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
import numpy as np

from backend.database.models import TigerImage, Tiger
from backend.database.vector_search import (
    store_embedding,
    find_matching_tigers,
)
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for embedding-related operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def store_image_embedding(
        self,
        image_id: UUID,
        embedding: np.ndarray
    ) -> bool:
        """Store embedding vector for an image"""
        return store_embedding(self.session, str(image_id), embedding)
    
    def find_matching_tigers_by_embedding(
        self,
        query_embedding: np.ndarray,
        tiger_id: Optional[UUID] = None,
        side_view: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """Find matching tigers based on embedding similarity"""
        return find_matching_tigers(
            self.session,
            query_embedding,
            str(tiger_id) if tiger_id else None,
            side_view,
            limit,
            similarity_threshold
        )
    
    def search_similar_images(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """Search for similar images using embedding"""
        # Use find_matching_tigers which queries vec_embeddings
        return find_matching_tigers(
            self.session,
            query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
    
    def get_image_embedding(self, image_id: UUID) -> Optional[np.ndarray]:
        """Get embedding vector for an image"""
        image = self.session.query(TigerImage).filter(
            TigerImage.image_id == image_id
        ).first()
        
        if image and image.embedding:
            # Note: embeddings now stored in vec_embeddings table, not in tiger_images
            return np.array(image.embedding)
        
        return None
    
    def update_image_embedding(
        self,
        image_id: UUID,
        embedding: np.ndarray,
        side_view: Optional[str] = None
    ) -> bool:
        """
        Update embedding for an image.

        Args:
            image_id: UUID of the image to update
            embedding: Embedding vector (numpy array)
            side_view: Optional side view identifier (e.g., 'left', 'right')

        Returns:
            True if update was successful, False if image not found

        Note:
            The embedding storage and side_view update are handled separately
            for transaction isolation. store_embedding commits its own transaction.
        """
        image = self.session.query(TigerImage).filter(
            TigerImage.image_id == image_id
        ).first()

        if not image:
            logger.warning(f"Image not found for embedding update: {image_id}")
            return False

        try:
            # Store embedding (this commits its own transaction)
            store_embedding(self.session, str(image_id), embedding)

            # Update side_view if provided (separate update)
            if side_view:
                image.side_view = side_view
                self.session.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to update embedding for image {image_id}: {e}")
            self.session.rollback()
            raise

    def fuse_multi_view_embeddings(
        self,
        embeddings: List[np.ndarray],
        method: str = "average"
    ) -> np.ndarray:
        """
        Fuse multiple embeddings from different views into a single embedding.

        This improves identification accuracy when multiple images of the same
        query tiger are available (e.g., left flank, right flank, different poses).

        Args:
            embeddings: List of embedding vectors (all must have same dimension)
            method: Fusion method - "average" (default), "max", or "weighted"

        Returns:
            Fused embedding vector (L2 normalized)
        """
        if not embeddings:
            raise ValueError("No embeddings provided for fusion")

        if len(embeddings) == 1:
            # Single embedding - just normalize and return
            embedding = embeddings[0]
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding

        # Stack embeddings
        embedding_stack = np.vstack(embeddings)

        # Apply fusion method
        if method == "average":
            # Average fusion (most common for ReID)
            fused = np.mean(embedding_stack, axis=0)
        elif method == "max":
            # Max pooling fusion
            fused = np.max(embedding_stack, axis=0)
        elif method == "weighted":
            # Weighted average based on embedding norms (higher norm = more confident)
            norms = np.linalg.norm(embedding_stack, axis=1, keepdims=True)
            weights = norms / np.sum(norms)
            fused = np.sum(embedding_stack * weights, axis=0)
        else:
            raise ValueError(f"Unknown fusion method: {method}")

        # L2 normalize the fused embedding
        norm = np.linalg.norm(fused)
        if norm > 0:
            fused = fused / norm

        logger.info(f"Fused {len(embeddings)} embeddings using {method} method")
        return fused

    def get_tiger_multi_view_embeddings(
        self,
        tiger_id: UUID,
        side_views: Optional[List[str]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Get all embeddings for a tiger, optionally filtered by side view.

        Args:
            tiger_id: Tiger UUID
            side_views: Optional list of side views to include
                       (e.g., ["left_flank", "right_flank"])

        Returns:
            Dictionary mapping image_id -> embedding
        """
        query = self.session.query(TigerImage).filter(
            TigerImage.tiger_id == tiger_id,
            TigerImage.embedding.isnot(None)
        )

        if side_views:
            query = query.filter(TigerImage.side_view.in_(side_views))

        images = query.all()

        embeddings = {}
        for image in images:
            if image.embedding is not None:
                embeddings[str(image.image_id)] = np.array(image.embedding)

        logger.info(f"Retrieved {len(embeddings)} embeddings for tiger {tiger_id}")
        return embeddings

    def get_fused_tiger_embedding(
        self,
        tiger_id: UUID,
        fusion_method: str = "average"
    ) -> Optional[np.ndarray]:
        """
        Get a fused embedding for a tiger from all their stored images.

        This creates a more robust representation by combining multiple views.

        Args:
            tiger_id: Tiger UUID
            fusion_method: How to combine embeddings ("average", "max", "weighted")

        Returns:
            Fused embedding or None if no embeddings found
        """
        embeddings_dict = self.get_tiger_multi_view_embeddings(tiger_id)

        if not embeddings_dict:
            return None

        embeddings = list(embeddings_dict.values())
        return self.fuse_multi_view_embeddings(embeddings, method=fusion_method)

    def find_matching_tigers_multi_view(
        self,
        query_embeddings: List[np.ndarray],
        limit: int = 5,
        similarity_threshold: float = 0.8,
        fusion_method: str = "average"
    ) -> List[Dict]:
        """
        Find matching tigers using multiple query embeddings (multi-view query).

        When multiple images of the query tiger are available, fuse them
        before matching for improved accuracy.

        Args:
            query_embeddings: List of query embeddings from different views
            limit: Maximum number of results
            similarity_threshold: Minimum similarity for a match
            fusion_method: How to fuse query embeddings

        Returns:
            List of match dictionaries
        """
        # Fuse query embeddings
        fused_query = self.fuse_multi_view_embeddings(
            query_embeddings,
            method=fusion_method
        )

        # Search with fused embedding
        return find_matching_tigers(
            self.session,
            fused_query,
            limit=limit,
            similarity_threshold=similarity_threshold
        )

    def filter_embedding_quality(
        self,
        embedding: np.ndarray,
        min_norm: float = 0.1,
        max_norm: float = 100.0,
        check_nan: bool = True,
        check_inf: bool = True
    ) -> Tuple[bool, str]:
        """
        Check if an embedding meets quality criteria.

        Args:
            embedding: Embedding vector to check
            min_norm: Minimum acceptable L2 norm
            max_norm: Maximum acceptable L2 norm
            check_nan: Whether to check for NaN values
            check_inf: Whether to check for infinite values

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        # Check for NaN
        if check_nan and np.any(np.isnan(embedding)):
            return False, "Embedding contains NaN values"

        # Check for infinity
        if check_inf and np.any(np.isinf(embedding)):
            return False, "Embedding contains infinite values"

        # Check norm
        norm = np.linalg.norm(embedding)
        if norm < min_norm:
            return False, f"Embedding norm ({norm:.4f}) below minimum ({min_norm})"
        if norm > max_norm:
            return False, f"Embedding norm ({norm:.4f}) above maximum ({max_norm})"

        # Check for all zeros
        if np.allclose(embedding, 0):
            return False, "Embedding is all zeros"

        return True, "OK"

    def store_embedding_with_quality_check(
        self,
        image_id: UUID,
        embedding: np.ndarray,
        detection_confidence: float = 0.0,
        min_detection_confidence: float = 0.8
    ) -> Tuple[bool, str]:
        """
        Store embedding only if it passes quality checks.

        Args:
            image_id: Image UUID
            embedding: Embedding vector
            detection_confidence: Confidence from tiger detection
            min_detection_confidence: Minimum detection confidence required

        Returns:
            Tuple of (success, message)
        """
        # Check detection confidence
        if detection_confidence < min_detection_confidence:
            return False, f"Detection confidence ({detection_confidence:.2f}) below threshold ({min_detection_confidence})"

        # Check embedding quality
        is_valid, reason = self.filter_embedding_quality(embedding)
        if not is_valid:
            return False, reason

        # Store the embedding
        success = self.store_image_embedding(image_id, embedding)
        if success:
            return True, "Embedding stored successfully"
        else:
            return False, "Failed to store embedding"

