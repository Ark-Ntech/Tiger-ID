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
from backend.services.tiger.model_loader import get_model_loader

logger = get_logger(__name__)


class TigerService:
    """Service for managing tiger identification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.detection_model = TigerDetectionModel()
        self.reid_model = TigerReIDModel()

        # Use centralized ModelLoader for model management
        self._model_loader = get_model_loader()

        # Initialize services
        self.inference_logger = get_inference_logger()
        self.cache_service = get_cache_service()

        # Auto-investigation settings
        auto_investigation = getattr(self.settings, 'auto_investigation', None)
        if auto_investigation and hasattr(auto_investigation, 'enabled'):
            self.auto_investigation_enabled = auto_investigation.enabled
        else:
            self.auto_investigation_enabled = False
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return self._model_loader.get_available_model_names()

    def _get_model(self, model_name: Optional[str] = None):
        """Get model instance by name.

        Args:
            model_name: Name of model to get (uses default 'wildlife_tools' if None)

        Returns:
            Model instance

        Raises:
            ValueError: If model is not available
        """
        return self._model_loader.get_model(model_name)
    
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
        
        # Check for ensemble mode
        ensemble_mode = getattr(self, '_ensemble_mode', None)
        
        if ensemble_mode == 'staggered':
            # Use staggered ensemble
            return await self.identify_with_staggered_ensemble(
                tiger_crop, similarity_threshold, user_id
            )
        elif ensemble_mode == 'parallel' or use_all_models:
            # Use parallel ensemble
            return await self.identify_with_parallel_ensemble(
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
    
    async def identify_with_staggered_ensemble(
        self,
        tiger_crop: bytes,
        similarity_threshold: float,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Identify tiger using staggered ensemble with confidence-based early exit.
        
        Stages:
        1. RAPID: >0.90 accept, <0.60 reject, else continue
        2. Wildlife-Tools: >0.85 accept, <0.65 reject, else continue
        3. CVWC2019: >0.80 accept, else continue
        """
        from PIL import Image
        import io
        
        result = {
            "identified": False,
            "model_path": [],
            "confidence": 0.0,
            "tiger_id": None,
            "tiger_name": None,
            "matches": []
        }
        
        image_obj = Image.open(io.BytesIO(tiger_crop))
        
        # Stage 1: RAPID (fast screening)
        if 'rapid' in self.get_available_models():
            try:
                model = self._get_model('rapid')
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)
                
                matches = find_matching_tigers(
                    self.db,
                    query_embedding=embedding,
                    limit=5,
                    similarity_threshold=similarity_threshold
                )
                
                result["model_path"].append("rapid")
                
                if matches:
                    confidence = matches[0]["similarity"]
                    if confidence > 0.90:
                        # High confidence - accept immediately
                        result.update({
                            "identified": True,
                            "tiger_id": matches[0]["tiger_id"],
                            "tiger_name": matches[0]["tiger_name"],
                            "confidence": confidence,
                            "matches": matches
                        })
                        return result
                    elif confidence < 0.60:
                        # Low confidence - mark as new
                        result["message"] = "Tiger not found in database - new individual"
                        result["requires_verification"] = True
                        return result
                    # Else continue to next stage
            except Exception as e:
                logger.warning(f"RAPID model failed: {e}, continuing to next stage")
        
        # Stage 2: Wildlife-Tools (standard identification)
        if 'wildlife_tools' in self.get_available_models():
            try:
                model = self._get_model('wildlife_tools')
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)
                
                matches = find_matching_tigers(
                    self.db,
                    query_embedding=embedding,
                    limit=5,
                    similarity_threshold=similarity_threshold
                )
                
                result["model_path"].append("wildlife_tools")
                
                if matches:
                    confidence = matches[0]["similarity"]
                    if confidence > 0.85:
                        # High confidence - accept
                        result.update({
                            "identified": True,
                            "tiger_id": matches[0]["tiger_id"],
                            "tiger_name": matches[0]["tiger_name"],
                            "confidence": confidence,
                            "matches": matches
                        })
                        return result
                    elif confidence < 0.65:
                        # Low confidence - mark as new
                        result["message"] = "Tiger not found in database - new individual"
                        result["requires_verification"] = True
                        return result
                    # Else continue to next stage
            except Exception as e:
                logger.warning(f"Wildlife-Tools model failed: {e}, continuing to next stage")
        
        # Stage 3: CVWC2019 (pose-robust specialist)
        if 'cvwc2019' in self.get_available_models():
            try:
                model = self._get_model('cvwc2019')
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)
                
                matches = find_matching_tigers(
                    self.db,
                    query_embedding=embedding,
                    limit=5,
                    similarity_threshold=similarity_threshold
                )
                
                result["model_path"].append("cvwc2019")
                
                if matches:
                    confidence = matches[0]["similarity"]
                    if confidence > 0.80:
                        # Accept
                        result.update({
                            "identified": True,
                            "tiger_id": matches[0]["tiger_id"],
                            "tiger_name": matches[0]["tiger_name"],
                            "confidence": confidence,
                            "matches": matches
                        })
                        return result
            except Exception as e:
                logger.warning(f"CVWC2019 model failed: {e}")
        
        # No match found
        result["message"] = "Tiger not found in database - new individual"
        result["requires_verification"] = True
        return result
    
    async def identify_with_parallel_ensemble(
        self,
        tiger_crop: bytes,
        similarity_threshold: float,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Identify tiger using parallel ensemble - run all models simultaneously.
        Use consensus decision logic to combine results.
        """
        import asyncio
        from PIL import Image
        import io
        
        image_obj = Image.open(io.BytesIO(tiger_crop))
        available_models = self.get_available_models()
        
        # Run all models in parallel
        async def run_model(model_name: str):
            try:
                model = self._get_model(model_name)
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)
                
                matches = find_matching_tigers(
                    self.db,
                    query_embedding=embedding,
                    limit=5,
                    similarity_threshold=similarity_threshold
                )
                
                return {
                    "model": model_name,
                    "matches": matches,
                    "best_similarity": matches[0]["similarity"] if matches else 0.0,
                    "tiger_id": matches[0]["tiger_id"] if matches else None,
                    "tiger_name": matches[0]["tiger_name"] if matches else None,
                    "success": True
                }
            except Exception as e:
                logger.error(f"Error with model {model_name}: {e}")
                return {
                    "model": model_name,
                    "error": str(e),
                    "success": False
                }
        
        # Run all models in parallel
        tasks = [run_model(model_name) for model_name in available_models]
        model_results = await asyncio.gather(*tasks)
        
        # Use consensus decision
        return self._consensus_decision(model_results)
    
    def _consensus_decision(self, model_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make consensus decision from multiple model results.
        
        Returns best match if models agree, or flags for human review if they disagree.
        """
        # Filter successful results
        successful_results = [r for r in model_results if r.get("success", False) and r.get("matches")]
        
        if not successful_results:
            return {
                "identified": False,
                "message": "Tiger not found in database - new individual",
                "requires_verification": True,
                "models": {r["model"]: r for r in model_results}
            }
        
        # Group by tiger_id
        tiger_votes = {}
        for result in successful_results:
            tiger_id = result.get("tiger_id")
            if tiger_id:
                if tiger_id not in tiger_votes:
                    tiger_votes[tiger_id] = {
                        "tiger_id": tiger_id,
                        "tiger_name": result.get("tiger_name"),
                        "votes": [],
                        "confidences": []
                    }
                tiger_votes[tiger_id]["votes"].append(result["model"])
                tiger_votes[tiger_id]["confidences"].append(result["best_similarity"])
        
        # Find tiger with most votes
        if tiger_votes:
            best_tiger = max(tiger_votes.values(), key=lambda x: len(x["votes"]))
            vote_count = len(best_tiger["votes"])
            total_models = len(successful_results)
            
            # Calculate average confidence
            avg_confidence = sum(best_tiger["confidences"]) / len(best_tiger["confidences"])
            
            # If majority agree (>50%), accept
            if vote_count > total_models / 2:
                return {
                    "identified": True,
                    "tiger_id": best_tiger["tiger_id"],
                    "tiger_name": best_tiger["tiger_name"],
                    "confidence": avg_confidence,
                    "consensus": True,
                    "vote_count": vote_count,
                    "total_models": total_models,
                    "models": {r["model"]: r for r in model_results}
                }
            else:
                # Split decision - flag for human review
                return {
                    "identified": False,
                    "message": "Models disagree - requires human review",
                    "requires_verification": True,
                    "top_candidates": [
                        {
                            "tiger_id": t["tiger_id"],
                            "tiger_name": t["tiger_name"],
                            "votes": len(t["votes"]),
                            "avg_confidence": sum(t["confidences"]) / len(t["confidences"])
                        }
                        for t in sorted(tiger_votes.values(), key=lambda x: len(x["votes"]), reverse=True)[:2]
                    ],
                    "models": {r["model"]: r for r in model_results}
                }
        
        return {
            "identified": False,
            "message": "Tiger not found in database - new individual",
            "requires_verification": True,
            "models": {r["model"]: r for r in model_results}
        }
    
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
    
    async def register_new_tiger(
        self,
        name: str,
        alias: Optional[str],
        images: List[UploadFile],
        notes: Optional[str],
        model_name: Optional[str],
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Register a new tiger with images.
        
        Args:
            name: Tiger name
            alias: Tiger alias/identifier
            images: List of image files
            notes: Additional notes
            model_name: Model to use for embedding generation
            user_id: User ID who registered the tiger
            
        Returns:
            Dictionary with created tiger information
        """
        from uuid import uuid4
        from pathlib import Path
        import os
        import shutil
        
        logger.info(f"Registering new tiger: {name} (alias: {alias}) with {len(images)} images")
        
        # Create tiger record
        tiger = Tiger(
            tiger_id=uuid4(),
            name=name,
            alias=alias,
            status="active",
            notes=notes,
            tags=["user-registered"]
        )
        
        self.db.add(tiger)
        self.db.flush()  # Get ID without committing
        
        # Process images
        image_paths = []
        for idx, image_file in enumerate(images):
            try:
                # Read image
                image_bytes = await image_file.read()
                await image_file.seek(0)
                
                # Detect tiger in image
                detection_result = await self.detection_model.detect(image_bytes)
                
                if not detection_result.get("detections"):
                    logger.warning(f"No tiger detected in image {image_file.filename}, skipping")
                    continue
                
                # Extract tiger crop
                tiger_crop = detection_result["detections"][0].get("crop")
                
                # Save image to storage
                storage_dir = Path("data/storage/tigers") / str(tiger.tiger_id)
                storage_dir.mkdir(parents=True, exist_ok=True)
                
                image_filename = f"{idx}_{image_file.filename}"
                image_path = storage_dir / image_filename
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                image_paths.append(str(image_path))
                
                # Generate embedding using selected model
                reid_model = self._get_model(model_name)
                
                if hasattr(reid_model, 'generate_embedding_from_bytes'):
                    embedding = await reid_model.generate_embedding_from_bytes(tiger_crop)
                else:
                    from PIL import Image
                    import io
                    image_obj = Image.open(io.BytesIO(tiger_crop))
                    embedding = await reid_model.generate_embedding(image_obj)
                
                # Create TigerImage record
                tiger_image = TigerImage(
                    tiger_id=tiger.tiger_id,
                    image_path=str(image_path),
                    uploaded_by=user_id,
                    meta_data={
                        "original_filename": image_file.filename,
                        "model_used": model_name or "wildlife_tools",
                        "registered_by": str(user_id)
                    }
                )
                
                self.db.add(tiger_image)
                self.db.flush()
                
                # Store embedding in vector database
                if embedding is not None:
                    store_embedding(
                        self.db,
                        tiger_id=str(tiger.tiger_id),
                        image_id=str(tiger_image.image_id),
                        embedding=embedding
                    )
                
                logger.info(f"Processed image {idx+1}/{len(images)} for tiger {tiger.tiger_id}")
                
            except Exception as e:
                logger.error(f"Error processing image {image_file.filename}: {e}", exc_info=True)
                continue
        
        # Commit all changes
        self.db.commit()
        self.db.refresh(tiger)
        
        logger.info(f"Successfully registered tiger {tiger.tiger_id} with {len(image_paths)} images")
        
        return {
            "tiger_id": str(tiger.tiger_id),
            "name": tiger.name,
            "alias": tiger.alias,
            "image_count": len(image_paths),
            "images": image_paths
        }
    
    async def get_tiger(self, tiger_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tiger details with images"""
        tiger = self.db.query(Tiger).filter(Tiger.tiger_id == tiger_id).first()
        
        if not tiger:
            return None
        
        images = self.db.query(TigerImage).filter(
            TigerImage.tiger_id == tiger_id
        ).all()
        
        # Format images for response
        image_list = []
        for img in images:
            image_list.append({
                "id": str(img.image_id),
                "url": img.image_path if img.image_path.startswith('http') else f"/api/v1/tigers/{tiger_id}/images/{img.image_id}",
                "path": img.image_path,
                "uploaded_by": str(img.uploaded_by) if img.uploaded_by else None,
                "meta_data": img.meta_data or {}
            })
        
        # Get related tigers (same facility or similar patterns)
        related_tigers = []
        if tiger.origin_facility_id:
            facility_tigers = self.db.query(Tiger).filter(
                Tiger.origin_facility_id == tiger.origin_facility_id,
                Tiger.tiger_id != tiger_id
            ).limit(5).all()
            
            for related_tiger in facility_tigers:
                related_tigers.append({
                    "tiger_id": str(related_tiger.tiger_id),
                    "id": str(related_tiger.tiger_id),
                    "name": related_tiger.name,
                    "alias": related_tiger.alias,
                    "status": related_tiger.status.value if hasattr(related_tiger.status, 'value') else str(related_tiger.status)
                })
        
        return {
            "tiger_id": str(tiger.tiger_id),
            "id": str(tiger.tiger_id),  # For frontend compatibility
            "name": tiger.name,
            "alias": tiger.alias,
            "status": tiger.status.value if hasattr(tiger.status, 'value') else str(tiger.status),
            "last_seen_location": tiger.last_seen_location,
            "last_seen_date": tiger.last_seen_date.isoformat() if tiger.last_seen_date else None,
            "image_count": len(images),
            "images": image_list,
            "notes": tiger.notes,
            "related_tigers": related_tigers,
            "origin_facility_id": str(tiger.origin_facility_id) if tiger.origin_facility_id else None
        }
