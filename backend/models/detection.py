"""MegaDetector v5 integration for tiger detection using Modal"""

from PIL import Image
import numpy as np
from typing import List, Dict, Any, Optional
import io

from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client
from backend.config.settings import get_settings
from backend.models.interfaces.base_detection_model import BaseDetectionModel

logger = get_logger(__name__)


class TigerDetectionModel(BaseDetectionModel):
    """MegaDetector v5 wrapper for tiger detection using Modal"""

    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize MegaDetector v5 model (Modal-based).

        Args:
            model_path: Path to model checkpoint (deprecated, kept for compatibility)
            device: Device to run model on (deprecated, kept for compatibility)
        """
        settings = get_settings()
        self.model_path = model_path or settings.models.detection.path
        self._confidence_threshold = settings.models.detection.confidence_threshold
        self.nms_threshold = settings.models.detection.nms_threshold
        self.modal_client = get_modal_client()

        logger.info("TigerDetectionModel initialized with Modal backend")

    @property
    def default_confidence_threshold(self) -> float:
        """Get the default confidence threshold."""
        return self._confidence_threshold

    @property
    def confidence_threshold(self) -> float:
        """Get the confidence threshold."""
        return self._confidence_threshold

    @property
    def supported_categories(self) -> List[str]:
        """Get supported detection categories."""
        return ["animal", "tiger"]
    
    async def load_model(self):
        """
        Load the detection model (no-op for Modal backend).
        
        Model is loaded on Modal containers automatically.
        """
        logger.info("Model loading handled by Modal backend")
        pass
    
    async def detect(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect tigers in an image using Modal.
        
        Args:
            image_bytes: Image bytes
            
        Returns:
            Dictionary with detections including bounding boxes and crops
        """
        try:
            # Load image for cropping
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # Call Modal service
            result = await self.modal_client.megadetector_detect(
                image,
                confidence_threshold=self.confidence_threshold
            )
            
            if result.get("success"):
                # Process detections from Modal
                detections = []
                for detection in result.get("detections", []):
                    # Extract bbox coordinates
                    bbox = detection.get("bbox", [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                        
                        # Ensure coordinates are within image bounds
                        x1 = max(0, min(x1, original_size[0]))
                        y1 = max(0, min(y1, original_size[1]))
                        x2 = max(0, min(x2, original_size[0]))
                        y2 = max(0, min(y2, original_size[1]))
                        
                        # Crop tiger from image
                        crop = image.crop((x1, y1, x2, y2))
                        
                        detections.append({
                            "bbox": [float(x1), float(y1), float(x2), float(y2)],
                            "confidence": float(detection.get("confidence", 0.0)),
                            "crop": crop,
                            "original_size": original_size,
                            "category": detection.get("category", "animal"),
                            "class_id": detection.get("class_id", 0)
                        })
                
                return {
                    "detections": detections,
                    "count": len(detections),
                    "image_size": original_size
                }
            else:
                error_msg = result.get("error", "Unknown error")
                
                # Check if request was queued
                if result.get("queued"):
                    logger.warning("Detection request queued for later processing")
                    return {
                        "detections": [],
                        "count": 0,
                        "queued": True,
                        "message": "Request queued for later processing"
                    }
                
                logger.error(f"Modal detection failed: {error_msg}")
                return {
                    "detections": [],
                    "count": 0,
                    "error": error_msg
                }
            
        except Exception as e:
            logger.error("Error during detection", error=str(e))
            return {
                "detections": [],
                "count": 0,
                "error": str(e)
            }
    
    async def detect_from_path(self, image_path: str) -> Dict[str, Any]:
        """Detect tigers from image file path"""
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        return await self.detect(image_bytes)

