"""Abstract base class for detection models.

All animal/tiger detection models must implement this interface
to ensure consistent behavior across different model backends.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image


@dataclass
class Detection:
    """Represents a single detection result.

    Attributes:
        bbox: Bounding box as [x1, y1, x2, y2] in pixel coordinates
        confidence: Detection confidence score (0.0 to 1.0)
        category: Detection category (e.g., 'animal', 'tiger')
        class_id: Numeric class identifier
        crop: Optional cropped image bytes of the detection
    """
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    category: str
    class_id: int
    crop: Optional[bytes] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "bbox": list(self.bbox),
            "confidence": self.confidence,
            "category": self.category,
            "class_id": self.class_id,
        }

    @property
    def width(self) -> int:
        """Get detection bounding box width."""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        """Get detection bounding box height."""
        return self.bbox[3] - self.bbox[1]

    @property
    def area(self) -> int:
        """Get detection bounding box area."""
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box."""
        cx = (self.bbox[0] + self.bbox[2]) / 2
        cy = (self.bbox[1] + self.bbox[3]) / 2
        return (cx, cy)


@dataclass
class DetectionResult:
    """Container for detection results.

    Attributes:
        detections: List of Detection objects
        image_size: Original image size as (width, height)
        model_name: Name of model that produced results
        inference_time_ms: Inference time in milliseconds
    """
    detections: List[Detection]
    image_size: Tuple[int, int]
    model_name: str
    inference_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "detections": [d.to_dict() for d in self.detections],
            "image_size": list(self.image_size),
            "model_name": self.model_name,
            "inference_time_ms": self.inference_time_ms,
            "success": True,
        }

    @property
    def count(self) -> int:
        """Get number of detections."""
        return len(self.detections)

    def filter_by_confidence(self, threshold: float) -> "DetectionResult":
        """Filter detections by confidence threshold.

        Args:
            threshold: Minimum confidence to keep

        Returns:
            New DetectionResult with filtered detections
        """
        filtered = [d for d in self.detections if d.confidence >= threshold]
        return DetectionResult(
            detections=filtered,
            image_size=self.image_size,
            model_name=self.model_name,
            inference_time_ms=self.inference_time_ms,
        )

    def filter_by_category(self, category: str) -> "DetectionResult":
        """Filter detections by category.

        Args:
            category: Category to keep

        Returns:
            New DetectionResult with filtered detections
        """
        filtered = [d for d in self.detections if d.category == category]
        return DetectionResult(
            detections=filtered,
            image_size=self.image_size,
            model_name=self.model_name,
            inference_time_ms=self.inference_time_ms,
        )


class BaseDetectionModel(ABC):
    """Abstract base class for detection models.

    This interface defines the contract for all detection models,
    whether they run locally, on Modal, or any other backend.

    Attributes:
        model_name: Human-readable name of the model
        default_confidence_threshold: Default minimum confidence for detections
        supported_categories: List of categories this model can detect
    """

    @property
    def model_name(self) -> str:
        """Get the model name.

        Returns:
            Human-readable model name
        """
        return self.__class__.__name__

    @property
    def default_confidence_threshold(self) -> float:
        """Get the default confidence threshold.

        Returns:
            Default minimum confidence (0.0 to 1.0)
        """
        return 0.5

    @property
    def supported_categories(self) -> List[str]:
        """Get supported detection categories.

        Returns:
            List of category strings this model can detect
        """
        return ["animal"]

    @abstractmethod
    async def load_model(self) -> None:
        """Load the model weights and prepare for inference.

        This method should be idempotent - calling it multiple times
        should not cause issues.

        For Modal-backed models, this may be a no-op since the model
        is loaded on the remote container.
        """
        pass

    @abstractmethod
    async def detect(
        self,
        image_bytes: bytes,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Detect objects in an image.

        Args:
            image_bytes: Raw image bytes
            confidence_threshold: Minimum confidence for detections
                                 (uses default if None)

        Returns:
            Dictionary with detection results:
                {
                    "success": bool,
                    "detections": List[Dict] with bbox, confidence, category, class_id,
                    "image_size": [width, height],
                    ...
                }

        Raises:
            RuntimeError: If detection fails
        """
        pass

    async def detect_image(
        self,
        image: Image.Image,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Detect objects in a PIL Image.

        Convenience method that converts PIL Image to bytes
        and delegates to detect.

        Args:
            image: PIL Image object
            confidence_threshold: Minimum confidence for detections

        Returns:
            Dictionary with detection results
        """
        import io
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return await self.detect(buffer.getvalue(), confidence_threshold)

    async def detect_and_crop(
        self,
        image_bytes: bytes,
        confidence_threshold: Optional[float] = None,
        return_all: bool = False
    ) -> List[bytes]:
        """Detect objects and return cropped images.

        Args:
            image_bytes: Raw image bytes
            confidence_threshold: Minimum confidence for detections
            return_all: If True, return all detections; otherwise just best

        Returns:
            List of cropped image bytes
        """
        import io
        from PIL import Image

        result = await self.detect(image_bytes, confidence_threshold)

        if not result.get("success") or not result.get("detections"):
            return []

        # Load original image
        image = Image.open(io.BytesIO(image_bytes))

        crops = []
        detections = result["detections"]

        if not return_all:
            # Sort by confidence and take best
            detections = sorted(
                detections,
                key=lambda d: d.get("confidence", 0),
                reverse=True
            )[:1]

        for detection in detections:
            bbox = detection.get("bbox", [])
            if len(bbox) >= 4:
                x1, y1, x2, y2 = bbox[:4]
                crop = image.crop((x1, y1, x2, y2))

                buffer = io.BytesIO()
                crop.save(buffer, format='JPEG')
                crops.append(buffer.getvalue())

        return crops

    async def batch_detect(
        self,
        images: List[bytes],
        confidence_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Detect objects in multiple images.

        Default implementation processes images sequentially.
        Subclasses may override for batch optimization.

        Args:
            images: List of raw image bytes
            confidence_threshold: Minimum confidence for detections

        Returns:
            List of detection result dictionaries
        """
        results = []
        for image_bytes in images:
            result = await self.detect(image_bytes, confidence_threshold)
            results.append(result)
        return results
