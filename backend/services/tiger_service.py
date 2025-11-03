"""Tiger service for business logic"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import UploadFile
import numpy as np

from backend.database import Tiger, TigerImage, get_db_session
from backend.database.vector_search import find_matching_tigers, store_embedding
from backend.models.reid import TigerReIDModel
from backend.models.detection import TigerDetectionModel
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class TigerService:
    """Service for managing tiger identification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.detection_model = TigerDetectionModel()
        self.reid_model = TigerReIDModel()
        # Initialize models asynchronously when needed
    
    async def identify_tiger_from_image(
        self,
        image: UploadFile,
        user_id: UUID,
        similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Identify a tiger from an uploaded image"""
        logger.info("Identifying tiger from image", filename=image.filename)
        
        # Read image
        image_bytes = await image.read()
        
        # Detect tiger in image
        detection_result = await self.detection_model.detect(image_bytes)
        
        if not detection_result.get("detections"):
            return {
                "identified": False,
                "message": "No tiger detected in image",
                "confidence": 0.0
            }
        
        # Extract tiger crop
        tiger_crop = detection_result["detections"][0].get("crop")
        
        # Generate embedding
        embedding = await self.reid_model.generate_embedding(tiger_crop)
        
        # Search for matching tigers
        matches = find_matching_tigers(
            self.db,
            query_embedding=embedding,
            limit=5,
            similarity_threshold=similarity_threshold
        )
        
        if matches:
            best_match = matches[0]
            return {
                "identified": True,
                "tiger_id": best_match["tiger_id"],
                "tiger_name": best_match["tiger_name"],
                "similarity": best_match["similarity"],
                "confidence": best_match["similarity"],
                "matches": matches
            }
        
        # New tiger - create placeholder
        return {
            "identified": False,
            "message": "Tiger not found in database - new individual",
            "confidence": 0.0,
            "requires_verification": True
        }
    
    async def store_tiger_image(
        self,
        tiger_id: UUID,
        image_path: str,
        embedding: np.ndarray,
        side_view: str = "unknown",
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Store a tiger image with embedding"""
        with get_db_session() as session:
            image = TigerImage(
                tiger_id=tiger_id,
                image_path=image_path,
                side_view=side_view,
                uploaded_by=user_id
            )
            session.add(image)
            session.commit()
            session.refresh(image)
            
            # Store embedding
            store_embedding(session, str(image.image_id), embedding)
            
            return {
                "image_id": str(image.image_id),
                "tiger_id": str(tiger_id),
                "image_path": image_path
            }
    
    async def get_tiger(self, tiger_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tiger details"""
        tiger = self.db.query(Tiger).filter(Tiger.tiger_id == tiger_id).first()
        
        if not tiger:
            return None
        
        images = self.db.query(TigerImage).filter(
            TigerImage.tiger_id == tiger_id
        ).all()
        
        return {
            "tiger_id": str(tiger.tiger_id),
            "name": tiger.name,
            "alias": tiger.alias,
            "status": tiger.status,
            "last_seen_location": tiger.last_seen_location,
            "last_seen_date": tiger.last_seen_date.isoformat() if tiger.last_seen_date else None,
            "image_count": len(images)
        }
