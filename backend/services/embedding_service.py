"""Service layer for image embedding operations"""

from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.orm import Session
import numpy as np

from backend.database.models import TigerImage
from backend.database.vector_search import (
    store_embedding,
    find_matching_tigers,
    search_similar_embeddings
)


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
    ) -> List[tuple]:
        """Search for similar images using embedding"""
        return search_similar_embeddings(
            self.session,
            query_embedding,
            "tiger_images",
            limit,
            similarity_threshold
        )
    
    def get_image_embedding(self, image_id: UUID) -> Optional[np.ndarray]:
        """Get embedding vector for an image"""
        image = self.session.query(TigerImage).filter(
            TigerImage.image_id == image_id
        ).first()
        
        if image and image.embedding:
            # Convert pgvector to numpy array
            return np.array(image.embedding)
        
        return None
    
    def update_image_embedding(
        self,
        image_id: UUID,
        embedding: np.ndarray,
        side_view: Optional[str] = None
    ) -> bool:
        """Update embedding for an image"""
        image = self.session.query(TigerImage).filter(
            TigerImage.image_id == image_id
        ).first()
        
        if not image:
            return False
        
        # Store embedding
        store_embedding(self.session, str(image_id), embedding)
        
        # Update side_view if provided
        if side_view:
            image.side_view = side_view
            self.session.commit()
        
        return True

