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
from backend.config.settings import get_settings
from backend.services.model_inference_logger import get_inference_logger
from backend.services.model_cache_service import get_cache_service

logger = get_logger(__name__)


class TigerService:
    """Service for managing tiger identification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.detection_model = TigerDetectionModel()
        self.reid_model = TigerReIDModel()
        # Initialize models asynchronously when needed
        self._available_models = {}
        self._initialize_available_models()
        
        # Initialize services
        self.inference_logger = get_inference_logger()
        self.cache_service = get_cache_service()
        
        # Auto-investigation settings
        auto_investigation = getattr(self.settings, 'auto_investigation', None)
        if auto_investigation and hasattr(auto_investigation, 'enabled'):
            self.auto_investigation_enabled = auto_investigation.enabled
        else:
            self.auto_investigation_enabled = False
    
    def _initialize_available_models(self):
        """Initialize available RE-ID models (all run on Modal)"""
        self._available_models = {
            'tiger_reid': TigerReIDModel
        }
        
        # All models now use Modal backend - import them all
        try:
            from backend.models.wildlife_tools import WildlifeToolsReIDModel
            self._available_models['wildlife_tools'] = WildlifeToolsReIDModel
            logger.info("WildlifeTools model available (Modal)")
        except ImportError as e:
            logger.debug(f"WildlifeToolsReIDModel not available: {e}")
        
        try:
            from backend.models.cvwc2019_reid import CVWC2019ReIDModel
            self._available_models['cvwc2019'] = CVWC2019ReIDModel
            logger.info("CVWC2019 model available (Modal)")
        except ImportError as e:
            logger.debug(f"CVWC2019ReIDModel not available: {e}")
        
        try:
            from backend.models.rapid_reid import RAPIDReIDModel
            self._available_models['rapid'] = RAPIDReIDModel
            logger.info("RAPID model available (Modal)")
        except ImportError as e:
            logger.debug(f"RAPIDReIDModel not available: {e}")
        
        logger.info(f"Initialized {len(self._available_models)} Modal-powered models: {list(self._available_models.keys())}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self._available_models.keys())
    
    def _get_model(self, model_name: Optional[str] = None):
        """Get model instance by name"""
        if model_name is None:
            model_name = 'tiger_reid'  # Default model
        
        if model_name not in self._available_models:
            raise ValueError(f"Model '{model_name}' not available. Available: {self.get_available_models()}")
        
        model_class = self._available_models[model_name]
        return model_class()
    
    async def identify_tiger_from_image(
        self,
        image: UploadFile,
        user_id: UUID,
        similarity_threshold: float = 0.8,
        model_name: Optional[str] = None,
        use_all_models: bool = False
    ) -> Dict[str, Any]:
        """
        Identify a tiger from an uploaded image
        
        Args:
            image: Uploaded image file
            user_id: User ID
            similarity_threshold: Similarity threshold for matching
            model_name: Name of model to use (None for default)
            use_all_models: If True, run all available models and return combined results
            
        Returns:
            Dictionary with identification results
        """
        logger.info("Identifying tiger from image", filename=image.filename, model=model_name)
        
        # Read image
        image_bytes = await image.read()
        
        # Detect tiger in image
        detection_result = await self.detection_model.detect(image_bytes)
        
        if not detection_result.get("detections"):
            return {
                "identified": False,
                "message": "No tiger detected in image",
                "confidence": 0.0,
                "model": model_name or "default"
            }
        
        # Extract tiger crop
        tiger_crop = detection_result["detections"][0].get("crop")
        
        if use_all_models:
            # Run all available models
            return await self._identify_with_all_models(
                tiger_crop, similarity_threshold, user_id
            )
        else:
            # Use specified or default model
            reid_model = self._get_model(model_name)
            
            # Generate embedding
            if hasattr(reid_model, 'generate_embedding_from_bytes'):
                embedding = await reid_model.generate_embedding_from_bytes(tiger_crop)
            else:
                from PIL import Image
                import io
                image_obj = Image.open(io.BytesIO(tiger_crop))
                embedding = await reid_model.generate_embedding(image_obj)
            
            # Search for matching tigers
            matches = find_matching_tigers(
                self.db,
                query_embedding=embedding,
                limit=5,
                similarity_threshold=similarity_threshold
            )
            
            result = {
                "model": model_name or "tiger_reid",
                "identified": False,
                "confidence": 0.0
            }
            
            if matches:
                best_match = matches[0]
                result.update({
                    "identified": True,
                    "tiger_id": best_match["tiger_id"],
                    "tiger_name": best_match["tiger_name"],
                    "similarity": best_match["similarity"],
                    "confidence": best_match["similarity"],
                    "matches": matches
                })
            else:
                result.update({
                    "message": "Tiger not found in database - new individual",
                    "requires_verification": True
                })
            
            return result
    
    async def _identify_with_all_models(
        self,
        tiger_crop: bytes,
        similarity_threshold: float,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Identify using all available models"""
        from PIL import Image
        import io
        
        results = {
            "identified": False,
            "models": {},
            "best_match": None,
            "all_matches": []
        }
        
        image_obj = Image.open(io.BytesIO(tiger_crop))
        
        for model_name in self.get_available_models():
            try:
                model = self._get_model(model_name)
                
                # Generate embedding
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)
                
                # Search for matches
                matches = find_matching_tigers(
                    self.db,
                    query_embedding=embedding,
                    limit=5,
                    similarity_threshold=similarity_threshold
                )
                
                results["models"][model_name] = {
                    "matches": matches,
                    "best_similarity": matches[0]["similarity"] if matches else 0.0
                }
                
                # Track best match across all models
                if matches and (not results["best_match"] or matches[0]["similarity"] > results["best_match"]["similarity"]):
                    results["best_match"] = {
                        "model": model_name,
                        "tiger_id": matches[0]["tiger_id"],
                        "tiger_name": matches[0]["tiger_name"],
                        "similarity": matches[0]["similarity"]
                    }
                    results["identified"] = True
                    results["confidence"] = matches[0]["similarity"]
                
            except Exception as e:
                logger.error(f"Error with model {model_name}: {e}")
                results["models"][model_name] = {"error": str(e)}
        
        return results
    
    async def identify_tigers_batch(
        self,
        images: List[UploadFile],
        user_id: UUID,
        similarity_threshold: float = 0.8,
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify tigers from multiple images (batch processing)
        
        Args:
            images: List of uploaded image files
            user_id: User ID
            similarity_threshold: Similarity threshold for matching
            model_name: Name of model to use (None for default)
            
        Returns:
            List of identification results
        """
        logger.info(f"Batch identifying tigers from {len(images)} images")
        
        results = []
        
        for image in images:
            try:
                result = await self.identify_tiger_from_image(
                    image, user_id, similarity_threshold, model_name
                )
                result["image_filename"] = image.filename
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing image {image.filename}: {e}")
                results.append({
                    "image_filename": image.filename,
                    "identified": False,
                    "error": str(e)
                })
        
        return results
    
    async def store_tiger_image(
        self,
        tiger_id: UUID,
        image_path: str,
        embedding: np.ndarray,
        side_view: str = "unknown",
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Store a tiger image with embedding"""
        session = next(get_db_session())

        try:
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
        finally:
            session.close()
    
    async def _trigger_auto_investigation(
        self,
        identification_result: Dict[str, Any],
        user_id: UUID
    ) -> None:
        """
        Automatically trigger investigation when tiger is identified
        
        Args:
            identification_result: Tiger identification result
            user_id: User ID who triggered the identification
        """
        try:
            from backend.services.investigation_service import InvestigationService
            from backend.database.models import Investigation, InvestigationStatus
            
            tiger_id = identification_result.get("tiger_id")
            tiger_name = identification_result.get("tiger_name", "Unknown Tiger")
            confidence = identification_result.get("confidence", 0.0)
            
            if not tiger_id:
                return
            
            investigation_service = InvestigationService(self.db)
            
            # Create investigation
            investigation = investigation_service.create_investigation(
                title=f"Auto-Investigation: Tiger {tiger_name} Identified",
                description=(
                    f"Automatic investigation triggered by tiger identification. "
                    f"Tiger ID: {tiger_id}, Confidence: {confidence:.2%}"
                ),
                created_by=user_id,
                priority="medium" if confidence > 0.8 else "low",
                tags=["auto-generated", "tiger-identification"]
            )
            
            # Link tiger to investigation
            if investigation:
                investigation.related_tigers = [tiger_id]
                self.db.commit()
                
                logger.info(
                    f"Auto-investigation created for tiger {tiger_id}",
                    investigation_id=str(investigation.investigation_id),
                    confidence=confidence
                )
                
        except Exception as e:
            logger.error(f"Error triggering auto-investigation: {e}", exc_info=True)
    
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
