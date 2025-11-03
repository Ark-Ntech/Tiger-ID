"""MegaDetector v5 integration for tiger detection"""

import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from typing import List, Dict, Any, Optional
import io
import sys
from pathlib import Path

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)

# Add MegaDetector to path if available
MEGADETECTOR_PATH = Path(__file__).parent.parent.parent.parent / "data" / "models" / "megadetector"
if MEGADETECTOR_PATH.exists():
    sys.path.insert(0, str(MEGADETECTOR_PATH))


class TigerDetectionModel:
    """MegaDetector v5 wrapper for tiger detection"""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cuda"):
        """
        Initialize MegaDetector v5 model
        
        Args:
            model_path: Path to model checkpoint (defaults to config or downloads)
            device: Device to run model on (cuda or cpu)
        """
        self.device = device
        settings = get_settings()
        self.model_path = model_path or settings.models.detection.path
        self.model = None
        self.confidence_threshold = settings.models.detection.confidence_threshold
        self.nms_threshold = settings.models.detection.nms_threshold
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((640, 640)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    async def load_model(self):
        """Load the detection model"""
        if self.model is not None:
            return
        
        try:
            # Try to load MegaDetector if available
            if MEGADETECTOR_PATH.exists():
                try:
                    from megadetector.detection.run_detector import load_detector
                    
                    # Determine model path - try v5 first, then fallback
                    model_file = self.model_path
                    if not os.path.exists(model_file):
                        # Try common MegaDetector model names
                        possible_paths = [
                            "./data/models/md_v5a.0.0.pt",
                            "./data/models/megadetector_v5.pth",
                            "./data/models/md_v5a.0.0.pt",
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                model_file = path
                                break
                        
                        # If still not found, use model alias
                        if not os.path.exists(model_file):
                            model_file = "MDV5A"  # MegaDetector v5a alias
                    
                    logger.info(f"Loading MegaDetector from {model_file}")
                    self.model = load_detector(
                        model_file,
                        verbose=False
                    )
                    logger.info("MegaDetector loaded successfully")
                    return
                    
                except ImportError as e:
                    logger.warning(f"Could not import MegaDetector: {e}. Using fallback.")
                except Exception as e:
                    logger.warning(f"Failed to load MegaDetector: {e}. Using fallback.")
            
            # Fallback to YOLOv5 for animal detection
            logger.info("MegaDetector not available, using YOLOv5 fallback")
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.model.to(self.device)
            self.model.eval()
                
        except Exception as e:
            logger.error("Failed to load detection model", error=str(e))
            raise
    
    async def detect(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect tigers in an image
        
        Args:
            image_bytes: Image bytes
            
        Returns:
            Dictionary with detections including bounding boxes and crops
        """
        if self.model is None:
            await self.load_model()
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # Check if using MegaDetector or YOLOv5
            if hasattr(self.model, 'generate_detections_one_image'):
                # Using MegaDetector
                result = self.model.generate_detections_one_image(
                    img_original=image,
                    image_id="query_image",
                    detection_threshold=self.confidence_threshold,
                    verbose=False
                )
                
                # Extract detections from result
                detections_list = result.get('detections', []) if result.get('failure') is None else []
                
                detections = []
                for detection in detections_list:
                    # MegaDetector returns detections with:
                    # detection['category'] = '1' (animal), '2' (person), '3' (vehicle)
                    # detection['conf'] = confidence
                    # detection['bbox'] = [xmin, ymin, width, height] in normalized coordinates
                    if detection.get('category') == '1':  # Animal class
                        bbox = detection['bbox']
                        # Convert normalized [x, y, w, h] to absolute [x1, y1, x2, y2]
                        x1 = bbox[0] * original_size[0]
                        y1 = bbox[1] * original_size[1]
                        x2 = (bbox[0] + bbox[2]) * original_size[0]
                        y2 = (bbox[1] + bbox[3]) * original_size[1]
                        
                        # Ensure coordinates are within image bounds
                        x1 = max(0, min(x1, original_size[0]))
                        y1 = max(0, min(y1, original_size[1]))
                        x2 = max(0, min(x2, original_size[0]))
                        y2 = max(0, min(y2, original_size[1]))
                        
                        # Crop tiger from image
                        crop = image.crop((x1, y1, x2, y2))
                        
                        detections.append({
                            "bbox": [float(x1), float(y1), float(x2), float(y2)],
                            "confidence": float(detection['conf']),
                            "crop": crop,
                            "original_size": original_size,
                            "category": "animal"
                        })
                
                if result.get('failure'):
                    logger.warning(f"Detection failed: {result['failure']}")
                
            else:
                # Using YOLOv5 fallback
                results = self.model(image)
                
                # Parse results
                detections = []
                if hasattr(results, 'pandas') and results.pandas().xyxy[0] is not None:
                    df = results.pandas().xyxy[0]
                    
                    # Filter for animals (YOLOv5 uses different class IDs)
                    # Class 0 = person, we want animals - use a broader filter
                    # Note: YOLOv5 doesn't have a generic "animal" class, so we filter by confidence
                    for _, detection in df.iterrows():
                        if detection['confidence'] >= self.confidence_threshold:
                            x1, y1, x2, y2 = detection['xmin'], detection['ymin'], detection['xmax'], detection['ymax']
                            
                            # Crop from image
                            crop = image.crop((x1, y1, x2, y2))
                            
                            detections.append({
                                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                                "confidence": float(detection['confidence']),
                                "crop": crop,
                                "original_size": original_size,
                                "class": int(detection['class']),
                                "name": detection.get('name', 'unknown')
                            })
            
            return {
                "detections": detections,
                "count": len(detections),
                "image_size": original_size
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

