"""Tiger identification service.

Handles tiger identification from images using various ReID models.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncio
from sqlalchemy.orm import Session
from fastapi import UploadFile
from PIL import Image
import io

from backend.utils.logging import get_logger
from backend.config.settings import get_settings
from backend.database.vector_search import find_matching_tigers
from backend.models.detection import TigerDetectionModel
from backend.models.interfaces.base_reid_model import BaseReIDModel
from backend.services.tiger.model_loader import get_model_loader
from backend.services.tiger.ensemble_strategy import (
    EnsembleStrategy,
    StaggeredEnsembleStrategy,
    ParallelEnsembleStrategy,
    WeightedEnsembleStrategy,
    VerifiedEnsembleStrategy,
)
from backend.services.model_inference_logger import get_inference_logger
from backend.services.model_cache_service import get_cache_service

logger = get_logger(__name__)


class TigerIdentificationService:
    """Service for identifying tigers from images."""

    def __init__(
        self,
        db: Session,
        detection_model: Optional[TigerDetectionModel] = None
    ):
        """Initialize identification service.

        Args:
            db: Database session
            detection_model: Optional detection model (creates default if not provided)
        """
        self.db = db
        self.settings = get_settings()
        self.detection_model = detection_model or TigerDetectionModel()

        # Initialize auxiliary services
        self.inference_logger = get_inference_logger()
        self.cache_service = get_cache_service()

        # Use centralized ModelLoader for model management
        self._model_loader = get_model_loader()

        # Ensemble settings
        self._ensemble_mode: Optional[str] = None

    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        return self._model_loader.get_available_model_names()

    def _get_model(self, model_name: Optional[str] = None) -> BaseReIDModel:
        """Get model instance by name.

        Args:
            model_name: Name of model to get (uses default if None)

        Returns:
            Model instance

        Raises:
            ValueError: If model name is not available
        """
        return self._model_loader.get_model(model_name)

    def _get_all_model_instances(self) -> Dict[str, BaseReIDModel]:
        """Get dictionary of all available model instances."""
        return self._model_loader.get_all_model_instances()

    def set_ensemble_mode(self, mode: Optional[str]):
        """Set the ensemble mode for identification.

        Args:
            mode: 'staggered', 'parallel', 'weighted', 'verified', or None for single model
        """
        if mode and mode not in ['staggered', 'parallel', 'weighted', 'verified']:
            raise ValueError(f"Invalid ensemble mode: {mode}")
        self._ensemble_mode = mode

    async def identify_from_image(
        self,
        image: UploadFile,
        user_id: UUID,
        similarity_threshold: float = 0.8,
        model_name: Optional[str] = None,
        use_all_models: bool = False
    ) -> Dict[str, Any]:
        """Identify a tiger from an uploaded image.

        Args:
            image: Uploaded image file
            user_id: User ID
            similarity_threshold: Similarity threshold for matching
            model_name: Name of model to use (None for default)
            use_all_models: If True, run all available models

        Returns:
            Dictionary with identification results
        """
        logger.info(
            "Identifying tiger from image",
            filename=image.filename,
            model=model_name
        )

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

        # Convert crop to bytes if it's a PIL Image
        # Use run_in_executor to avoid blocking the event loop
        if hasattr(tiger_crop, 'save'):
            def _save_image_to_bytes(img):
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG')
                return buffer.getvalue()

            loop = asyncio.get_event_loop()
            tiger_crop = await loop.run_in_executor(None, _save_image_to_bytes, tiger_crop)

        # Choose identification strategy
        if self._ensemble_mode == 'staggered':
            strategy = StaggeredEnsembleStrategy()
            models = self._get_all_model_instances()
            return await strategy.identify(
                tiger_crop, models, self.db, similarity_threshold, user_id
            )

        elif self._ensemble_mode == 'weighted':
            # Use weighted ensemble with calibration and re-ranking
            strategy = WeightedEnsembleStrategy(
                use_reranking=True,
                use_calibration=True
            )
            models = self._get_all_model_instances()
            return await strategy.identify(
                tiger_crop, models, self.db, similarity_threshold, user_id
            )

        elif self._ensemble_mode == 'verified':
            # Use verified ensemble with MatchAnything geometric verification
            strategy = VerifiedEnsembleStrategy(
                use_reranking=True,
                use_calibration=True,
                use_verification=True,
                use_adaptive_weights=True
            )
            models = self._get_all_model_instances()
            return await strategy.identify(
                tiger_crop, models, self.db, similarity_threshold, user_id
            )

        elif self._ensemble_mode == 'parallel' or use_all_models:
            strategy = ParallelEnsembleStrategy()
            models = self._get_all_model_instances()
            return await strategy.identify(
                tiger_crop, models, self.db, similarity_threshold, user_id
            )

        else:
            # Single model identification
            return await self._identify_single_model(
                tiger_crop, model_name, similarity_threshold
            )

    async def _identify_single_model(
        self,
        tiger_crop: bytes,
        model_name: Optional[str],
        similarity_threshold: float
    ) -> Dict[str, Any]:
        """Identify using a single model.

        Args:
            tiger_crop: Cropped tiger image bytes
            model_name: Model to use
            similarity_threshold: Minimum similarity for match

        Returns:
            Identification result dictionary
        """
        reid_model = self._get_model(model_name)

        # Generate embedding
        if hasattr(reid_model, 'generate_embedding_from_bytes'):
            embedding = await reid_model.generate_embedding_from_bytes(tiger_crop)
        else:
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

    async def identify_batch(
        self,
        images: List[UploadFile],
        user_id: UUID,
        similarity_threshold: float = 0.8,
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Identify tigers from multiple images.

        Args:
            images: List of uploaded image files
            user_id: User ID
            similarity_threshold: Similarity threshold for matching
            model_name: Name of model to use

        Returns:
            List of identification results
        """
        logger.info(f"Batch identifying tigers from {len(images)} images")

        results = []

        for image in images:
            try:
                result = await self.identify_from_image(
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
