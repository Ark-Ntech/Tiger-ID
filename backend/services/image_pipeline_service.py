"""
Image Pipeline Service

Processes discovered images through the tiger identification pipeline.

Pipeline steps:
1. Download image from URL
2. Quality check (OpenCV - local, no API)
3. Tiger detection (MegaDetector)
4. Crop detections
5. Generate embeddings (6-model ensemble on Modal GPU)
6. Database search for matches
7. Create/update tiger records

All image processing uses local tools (OpenCV, PIL).
ML inference uses existing Modal GPU infrastructure.
"""

import asyncio
import aiohttp
import hashlib
import io
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID, uuid4
from pathlib import Path
from dataclasses import dataclass

import numpy as np
from PIL import Image

from sqlalchemy.orm import Session

from backend.database.models import Tiger, TigerImage, Facility, TigerStatus, SideView
from backend.database.vector_search import find_matching_tigers, store_embedding
from backend.services.tiger_service import TigerService
from backend.services.facility_crawler_service import DiscoveredImage
from backend.services.investigation_trigger_service import InvestigationTriggerService
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

# Try to import OpenCV for quality assessment
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

logger = get_logger(__name__)


@dataclass
class QualityScore:
    """Image quality assessment result."""
    score: float  # 0-100
    blur_score: float
    resolution_score: float
    brightness_score: float
    contrast_score: float
    is_acceptable: bool
    issues: List[str]


@dataclass
class ProcessedTiger:
    """Result of processing a tiger image."""
    tiger: Tiger
    tiger_image: TigerImage
    is_new: bool
    match_similarity: Optional[float]
    detection_confidence: float


class ImagePipelineService:
    """
    Processes discovered images through the full tiger identification pipeline.

    Uses only FREE/local tools for image processing:
    - OpenCV for quality assessment
    - PIL for image manipulation
    - MegaDetector for tiger detection (local or Modal)
    - 6-model ensemble for ReID (Modal GPU)
    """

    # Quality thresholds
    MIN_QUALITY_SCORE = 40.0
    MIN_RESOLUTION = 200  # minimum dimension in pixels
    MAX_BLUR_THRESHOLD = 100  # Laplacian variance threshold

    # Matching thresholds
    NEW_TIGER_THRESHOLD = 0.85  # Below this, create new tiger
    STRONG_MATCH_THRESHOLD = 0.90  # Above this, definitely same tiger

    def __init__(self, db_session: Session):
        """Initialize the image pipeline service."""
        self.db = db_session
        self.settings = get_settings()
        self.tiger_service = TigerService(db_session)
        self._session: Optional[aiohttp.ClientSession] = None

        # Investigation trigger service for auto-investigations
        self._trigger_service = InvestigationTriggerService(db_session)

        # Image storage directory
        self.storage_path = Path(self.settings.storage.local_path if hasattr(self.settings, 'storage') else './data/storage')
        self.discovery_path = self.storage_path / 'discovered'
        self.discovery_path.mkdir(parents=True, exist_ok=True)

        # Processing statistics
        self._stats = {
            "images_processed": 0,
            "duplicates_skipped": 0,
            "quality_rejected": 0,
            "no_tigers_detected": 0,
            "embedding_failures": 0,
            "new_tigers": 0,
            "existing_tigers": 0,
            "investigations_triggered": 0,
        }

        logger.info(f"ImagePipelineService initialized (OpenCV available: {HAS_OPENCV})")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session is closed."""
        await self.close()
        return False

    def __del__(self):
        """Destructor - attempt to close session if not already closed."""
        if self._session is not None and not self._session.closed:
            # Can't await in destructor, but we can warn
            logger.warning(
                "ImagePipelineService session not properly closed. "
                "Use 'async with' or call close() explicitly."
            )

    def _compute_content_hash(self, image_bytes: bytes) -> str:
        """
        Compute SHA256 hash of image content for deduplication.

        Args:
            image_bytes: Raw image bytes

        Returns:
            64-character hexadecimal hash string
        """
        return hashlib.sha256(image_bytes).hexdigest()

    def _check_duplicate(self, content_hash: str) -> Optional[TigerImage]:
        """
        Check if an image with this content hash already exists.

        Args:
            content_hash: SHA256 hash of image content

        Returns:
            Existing TigerImage if duplicate found, None otherwise
        """
        existing = self.db.query(TigerImage).filter(
            TigerImage.content_hash == content_hash
        ).first()

        return existing

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self._stats.copy()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def process_discovered_images(
        self,
        images: List[DiscoveredImage],
        facility: Facility
    ) -> List[ProcessedTiger]:
        """
        Process all discovered images through the identification pipeline.

        Args:
            images: List of discovered images from crawler
            facility: Facility the images came from

        Returns:
            List of processed tigers (new and existing)
        """
        logger.info(f"Processing {len(images)} images for {facility.exhibitor_name}")

        processed_tigers: List[ProcessedTiger] = []

        for image in images:
            try:
                result = await self._process_single_image(image, facility)
                if result:
                    processed_tigers.append(result)

            except Exception as e:
                logger.warning(f"Failed to process image {image.url}: {e}")
                continue

        new_tigers = sum(1 for t in processed_tigers if t.is_new)
        logger.info(f"Processed {len(processed_tigers)} tigers ({new_tigers} new) for {facility.exhibitor_name}")

        return processed_tigers

    async def _process_single_image(
        self,
        image: DiscoveredImage,
        facility: Facility
    ) -> Optional[ProcessedTiger]:
        """
        Process a single discovered image.

        Args:
            image: Discovered image to process
            facility: Associated facility

        Returns:
            ProcessedTiger if successful, None otherwise
        """
        self._stats["images_processed"] += 1

        # 1. Download image
        image_bytes = await self._download_image(image.url)
        if not image_bytes:
            return None

        # 2. Check for duplicate BEFORE any ML processing (fast path)
        content_hash = self._compute_content_hash(image_bytes)
        existing_image = self._check_duplicate(content_hash)

        if existing_image:
            logger.debug(f"Duplicate image skipped: {image.url} (matches {existing_image.image_id})")
            self._stats["duplicates_skipped"] += 1
            return None

        # Store hash in image metadata for later use
        image.content_hash = content_hash

        # 3. Quality check
        quality = await self._assess_quality(image_bytes)
        if not quality.is_acceptable:
            logger.debug(f"Image rejected: {quality.issues}")
            self._stats["quality_rejected"] += 1
            return None

        # 3. Detect tigers
        detections = await self._detect_tigers(image_bytes)
        if not detections:
            logger.debug(f"No tigers detected in {image.url}")
            return None

        # Process first detection (strongest confidence)
        detection = detections[0]

        # 4. Crop detection
        cropped_bytes = self._crop_detection(image_bytes, detection)
        if not cropped_bytes:
            return None

        # 5. Generate embeddings
        embeddings = await self._generate_embeddings(cropped_bytes)
        if not embeddings:
            logger.warning(f"Failed to generate embeddings for {image.url}")
            return None

        # 6. Search for matches
        matches = await self._find_matches(embeddings)

        # 7. Create or update tiger record
        processed_tiger: ProcessedTiger
        if matches and matches[0].get("similarity", 0) > self.STRONG_MATCH_THRESHOLD:
            # Update existing tiger
            tiger, tiger_image = await self._update_existing_tiger(
                matches[0]["tiger_id"],
                cropped_bytes,
                embeddings,
                facility,
                image
            )
            processed_tiger = ProcessedTiger(
                tiger=tiger,
                tiger_image=tiger_image,
                is_new=False,
                match_similarity=matches[0]["similarity"],
                detection_confidence=detection.get("confidence", 0.0)
            )
        else:
            # Create new tiger
            tiger, tiger_image = await self._create_new_tiger(
                cropped_bytes,
                embeddings,
                facility,
                image,
                detection_confidence=detection.get("confidence", 0.0)
            )
            processed_tiger = ProcessedTiger(
                tiger=tiger,
                tiger_image=tiger_image,
                is_new=True,
                match_similarity=matches[0]["similarity"] if matches else None,
                detection_confidence=detection.get("confidence", 0.0)
            )

        # 8. Trigger auto-investigation if criteria met (fire-and-forget, non-blocking)
        await self._maybe_trigger_auto_investigation(
            processed_tiger=processed_tiger,
            image_bytes=image_bytes,
            facility=facility,
            quality_score=quality.score
        )

        return processed_tiger

    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            session = await self._get_session()

            async with session.get(url) as response:
                if response.status != 200:
                    logger.debug(f"Failed to download {url}: {response.status}")
                    return None

                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type:
                    logger.debug(f"Not an image: {url} ({content_type})")
                    return None

                return await response.read()

        except Exception as e:
            logger.debug(f"Download failed for {url}: {e}")
            return None

    async def _assess_quality(self, image_bytes: bytes) -> QualityScore:
        """
        Assess image quality using OpenCV (local, no API).

        Checks:
        - Resolution
        - Blur (Laplacian variance)
        - Brightness
        - Contrast
        """
        issues = []

        try:
            # Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)

            if HAS_OPENCV:
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    return QualityScore(
                        score=0, blur_score=0, resolution_score=0,
                        brightness_score=0, contrast_score=0,
                        is_acceptable=False, issues=["Failed to decode image"]
                    )

                height, width = img.shape[:2]
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # Blur score (Laplacian variance)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                blur_variance = laplacian.var()
                blur_score = min(100, blur_variance / 5)  # Normalize to 0-100

                if blur_variance < self.MAX_BLUR_THRESHOLD:
                    issues.append("Image is too blurry")

                # Resolution score
                min_dim = min(width, height)
                resolution_score = min(100, (min_dim / 1000) * 100)

                if min_dim < self.MIN_RESOLUTION:
                    issues.append(f"Resolution too low ({min_dim}px)")

                # Brightness score
                brightness = np.mean(gray)
                brightness_score = 100 - abs(128 - brightness) / 1.28  # Optimal around 128

                if brightness < 40:
                    issues.append("Image too dark")
                elif brightness > 215:
                    issues.append("Image too bright")

                # Contrast score
                contrast = gray.std()
                contrast_score = min(100, contrast / 0.7)

                if contrast < 30:
                    issues.append("Low contrast")

            else:
                # Fallback without OpenCV - use PIL
                pil_img = Image.open(io.BytesIO(image_bytes))
                width, height = pil_img.size

                min_dim = min(width, height)
                resolution_score = min(100, (min_dim / 1000) * 100)

                if min_dim < self.MIN_RESOLUTION:
                    issues.append(f"Resolution too low ({min_dim}px)")

                # Basic quality estimation without OpenCV
                blur_score = 50  # Unknown
                brightness_score = 50  # Unknown
                contrast_score = 50  # Unknown

            # Calculate overall score
            weights = {"blur": 0.3, "resolution": 0.3, "brightness": 0.2, "contrast": 0.2}
            overall_score = (
                blur_score * weights["blur"] +
                resolution_score * weights["resolution"] +
                brightness_score * weights["brightness"] +
                contrast_score * weights["contrast"]
            )

            return QualityScore(
                score=overall_score,
                blur_score=blur_score,
                resolution_score=resolution_score,
                brightness_score=brightness_score,
                contrast_score=contrast_score,
                is_acceptable=overall_score >= self.MIN_QUALITY_SCORE and len(issues) == 0,
                issues=issues
            )

        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return QualityScore(
                score=0, blur_score=0, resolution_score=0,
                brightness_score=0, contrast_score=0,
                is_acceptable=False, issues=[f"Assessment failed: {e}"]
            )

    async def _detect_tigers(self, image_bytes: bytes) -> List[Dict]:
        """
        Detect tigers in image using MegaDetector.

        Uses the existing detection model infrastructure.
        """
        try:
            detection_result = await self.tiger_service.detection_model.detect(image_bytes)
            return detection_result.get("detections", [])
        except Exception as e:
            logger.warning(f"Tiger detection failed: {e}")
            return []

    def _crop_detection(
        self,
        image_bytes: bytes,
        detection: Dict
    ) -> Optional[bytes]:
        """Crop detected tiger region from image."""
        try:
            # Get bounding box
            bbox = detection.get("bbox") or detection.get("bounding_box")
            if not bbox:
                # If no bbox, return original image
                return image_bytes

            # Load image with PIL
            pil_img = Image.open(io.BytesIO(image_bytes))
            width, height = pil_img.size

            # Handle different bbox formats
            if len(bbox) == 4:
                if all(0 <= b <= 1 for b in bbox):
                    # Normalized format [x, y, w, h]
                    x1 = int(bbox[0] * width)
                    y1 = int(bbox[1] * height)
                    x2 = int((bbox[0] + bbox[2]) * width)
                    y2 = int((bbox[1] + bbox[3]) * height)
                else:
                    # Absolute format [x1, y1, x2, y2] or [x, y, w, h]
                    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    if x2 < width / 2 and y2 < height / 2:
                        # It's [x, y, w, h]
                        x2 = x1 + x2
                        y2 = y1 + y2

            # Ensure valid bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)

            # Add some padding (10%)
            pad_x = int((x2 - x1) * 0.1)
            pad_y = int((y2 - y1) * 0.1)
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(width, x2 + pad_x)
            y2 = min(height, y2 + pad_y)

            # Crop
            cropped = pil_img.crop((x1, y1, x2, y2))

            # Convert back to bytes
            output = io.BytesIO()
            cropped.save(output, format='JPEG', quality=95)
            return output.getvalue()

        except Exception as e:
            logger.warning(f"Failed to crop detection: {e}")
            return image_bytes  # Return original if cropping fails

    async def _generate_embeddings(self, image_bytes: bytes) -> Optional[Dict[str, np.ndarray]]:
        """
        Generate embeddings using the 6-model ensemble on Modal GPU.

        Uses existing tiger_service infrastructure.
        """
        try:
            # Use wildlife_tools as primary model
            reid_model = self.tiger_service._get_model('wildlife_tools')
            embedding = await reid_model.get_embedding(image_bytes)

            if embedding is not None:
                return {"primary": embedding, "wildlife_tools": embedding}

            return None

        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None

    async def _find_matches(self, embeddings: Dict[str, np.ndarray]) -> List[Dict]:
        """
        Search database for matching tigers.

        Uses existing vector search infrastructure.
        """
        try:
            primary_embedding = embeddings.get("primary")
            if primary_embedding is None:
                return []

            matches = find_matching_tigers(
                self.db,
                primary_embedding,
                top_k=5,
                min_similarity=0.5
            )

            return matches

        except Exception as e:
            logger.warning(f"Match search failed: {e}")
            return []

    async def _create_new_tiger(
        self,
        image_bytes: bytes,
        embeddings: Dict[str, np.ndarray],
        facility: Facility,
        source_image: DiscoveredImage,
        detection_confidence: float
    ) -> Tuple[Tiger, TigerImage]:
        """Create a new tiger record from discovered image."""

        # Generate unique ID
        tiger_id = uuid4()

        # Generate name
        tiger_count = self.db.query(Tiger).filter(
            Tiger.origin_facility_id == facility.facility_id
        ).count()
        tiger_name = f"Tiger #{tiger_count + 1} - {facility.exhibitor_name}"

        # Save image
        image_path = self.discovery_path / f"{tiger_id}.jpg"
        image_path.write_bytes(image_bytes)

        # Create tiger record
        tiger = Tiger(
            tiger_id=tiger_id,
            name=tiger_name,
            origin_facility_id=facility.facility_id,
            last_seen_location=f"{facility.city}, {facility.state}" if facility.city else facility.state,
            last_seen_date=datetime.utcnow(),
            status=TigerStatus.active,
            is_reference=False,
            discovered_at=datetime.utcnow(),
            discovery_confidence=detection_confidence,
            tags=["discovered", "auto_crawl", "needs_review"],
            notes=f"Auto-discovered from {source_image.source_type} via continuous crawler"
        )
        self.db.add(tiger)
        self.db.flush()

        # Compute content hash for deduplication
        content_hash = self._compute_content_hash(image_bytes)

        # Create tiger image record
        tiger_image = TigerImage(
            image_id=uuid4(),
            tiger_id=tiger.tiger_id,
            image_path=str(image_path),
            embedding=embeddings.get("primary"),
            side_view=SideView.unknown,
            quality_score=detection_confidence * 100,
            verified=False,
            is_reference=False,
            content_hash=content_hash,  # For deduplication
            meta_data={
                "source": "continuous_discovery",
                "source_url": source_image.url,
                "source_page": source_image.source_url,
                "source_type": source_image.source_type,
                "facility_id": str(facility.facility_id),
                "discovered_at": datetime.utcnow().isoformat()
            }
        )
        self.db.add(tiger_image)

        # Store embedding in vector search
        store_embedding(self.db, tiger_image.image_id, embeddings.get("primary"))

        self.db.commit()
        self._stats["new_tigers"] += 1

        logger.info(f"[NEW TIGER] Created: {tiger_name} at {facility.exhibitor_name}")
        return (tiger, tiger_image)

    async def _update_existing_tiger(
        self,
        tiger_id: UUID,
        image_bytes: bytes,
        embeddings: Dict[str, np.ndarray],
        facility: Facility,
        source_image: DiscoveredImage
    ) -> Tuple[Tiger, TigerImage]:
        """Update an existing tiger with a new image."""

        tiger = self.db.query(Tiger).filter(Tiger.tiger_id == tiger_id).first()
        if not tiger:
            raise ValueError(f"Tiger {tiger_id} not found")

        # Update last seen
        tiger.last_seen_location = f"{facility.city}, {facility.state}" if facility.city else facility.state
        tiger.last_seen_date = datetime.utcnow()

        # Save new image
        image_id = uuid4()
        image_path = self.discovery_path / f"{image_id}.jpg"
        image_path.write_bytes(image_bytes)

        # Compute content hash for deduplication
        content_hash = self._compute_content_hash(image_bytes)

        # Create new tiger image record
        tiger_image = TigerImage(
            image_id=image_id,
            tiger_id=tiger.tiger_id,
            image_path=str(image_path),
            embedding=embeddings.get("primary"),
            side_view=SideView.unknown,
            verified=False,
            is_reference=False,
            content_hash=content_hash,  # For deduplication
            meta_data={
                "source": "continuous_discovery",
                "source_url": source_image.url,
                "source_page": source_image.source_url,
                "source_type": source_image.source_type,
                "facility_id": str(facility.facility_id),
                "discovered_at": datetime.utcnow().isoformat()
            }
        )
        self.db.add(tiger_image)

        # Store embedding
        store_embedding(self.db, tiger_image.image_id, embeddings.get("primary"))

        self.db.commit()
        self._stats["existing_tigers"] += 1

        logger.info(f"[TIGER UPDATE] New image added for {tiger.name}")
        return (tiger, tiger_image)

    async def _maybe_trigger_auto_investigation(
        self,
        processed_tiger: ProcessedTiger,
        image_bytes: bytes,
        facility: Facility,
        quality_score: float
    ):
        """
        Trigger auto-investigation if criteria are met.

        This method is FIRE-AND-FORGET - it queues the investigation
        for async background processing and returns immediately.
        Does NOT block the discovery pipeline.

        Args:
            processed_tiger: The processed tiger result
            image_bytes: Raw image bytes (full image, not cropped)
            facility: Associated facility
            quality_score: Image quality score (0-100)
        """
        try:
            # Only trigger for NEW tigers (not existing matches)
            if not processed_tiger.is_new:
                logger.debug(
                    f"[AUTO-TRIGGER] Skipping - tiger matched existing: "
                    f"{processed_tiger.tiger.name}"
                )
                return

            # Check trigger criteria (non-blocking)
            should_trigger, reason = await self._trigger_service.should_trigger_investigation(
                tiger_image=processed_tiger.tiger_image,
                facility=facility,
                detection_confidence=processed_tiger.detection_confidence,
                quality_score=quality_score
            )

            if not should_trigger:
                logger.debug(f"[AUTO-TRIGGER] Not triggered: {reason}")
                return

            # Trigger investigation (FIRE-AND-FORGET - queues for async processing)
            investigation = await self._trigger_service.trigger_investigation(
                tiger_image=processed_tiger.tiger_image,
                image_bytes=image_bytes,
                facility=facility,
                detection_confidence=processed_tiger.detection_confidence,
                quality_score=quality_score
            )

            if investigation:
                self._stats["investigations_triggered"] += 1
                logger.info(
                    f"[AUTO-TRIGGER] Investigation {str(investigation.investigation_id)[:8]} "
                    f"triggered for tiger at {facility.exhibitor_name}"
                )

        except Exception as e:
            # Log but don't block the pipeline
            logger.warning(f"[AUTO-TRIGGER] Failed to trigger investigation: {e}")

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()


# Convenience function
def get_image_pipeline_service(db_session: Session) -> ImagePipelineService:
    """Create and return an ImagePipelineService instance."""
    return ImagePipelineService(db_session)
