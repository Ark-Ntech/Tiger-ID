"""
Investigation Trigger Service

Manages automatic investigation triggering from the discovery pipeline.
Implements quality gates, rate limiting, and async queuing to prevent
investigation spam while catching important discoveries.

Key Design Decisions:
- Auto-investigations use DuckDuckGo deep research (free, no API key)
- All auto-investigations run completely async in background
- User uploads -> VerificationQueue with status="pending", requires_human_review=True
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.models import (
    Tiger, TigerImage, Facility, Investigation, VerificationQueue,
    InvestigationStatus, Priority, VerificationStatus
)
from backend.config.settings import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class InvestigationTriggerService:
    """
    Manages automatic investigation triggering from discovery pipeline.

    Implements:
    - Quality gates (image quality, detection confidence)
    - Rate limiting (global and per-facility)
    - Duplicate prevention (no re-investigating same image)
    - Async queuing via investigation2_task_runner
    """

    # Default configuration (can be overridden by settings.yaml)
    MIN_QUALITY_SCORE = 60.0        # Higher than pipeline threshold (40)
    MIN_DETECTION_CONFIDENCE = 0.85  # High confidence detections only
    MAX_INVESTIGATIONS_PER_HOUR = 5  # Rate limit
    MIN_TIME_BETWEEN_FACILITY = 3600  # 1 hour between same facility (seconds)

    def __init__(self, db_session: Session):
        """
        Initialize the investigation trigger service.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.settings = get_settings()

        # Load configuration from settings if available
        self._load_config()

        logger.info(
            f"InvestigationTriggerService initialized: "
            f"min_quality={self.MIN_QUALITY_SCORE}, "
            f"min_confidence={self.MIN_DETECTION_CONFIDENCE}, "
            f"max_per_hour={self.MAX_INVESTIGATIONS_PER_HOUR}"
        )

    def _load_config(self):
        """Load configuration from settings.yaml if available."""
        try:
            auto_config = getattr(self.settings, 'auto_investigation', None)
            if auto_config:
                if hasattr(auto_config, 'min_quality_score'):
                    self.MIN_QUALITY_SCORE = auto_config.min_quality_score
                if hasattr(auto_config, 'min_detection_confidence'):
                    self.MIN_DETECTION_CONFIDENCE = auto_config.min_detection_confidence
                if hasattr(auto_config, 'max_per_hour'):
                    self.MAX_INVESTIGATIONS_PER_HOUR = auto_config.max_per_hour
                if hasattr(auto_config, 'min_facility_interval_seconds'):
                    self.MIN_TIME_BETWEEN_FACILITY = auto_config.min_facility_interval_seconds
        except Exception as e:
            logger.warning(f"Failed to load auto_investigation config: {e}")

    def _count_recent_auto_investigations(self, hours: int = 1) -> int:
        """
        Count auto-investigations in the last N hours.

        Args:
            hours: Time window in hours

        Returns:
            Count of auto-investigations
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        count = self.db.query(func.count(Investigation.investigation_id)).filter(
            Investigation.source == "auto_discovery",
            Investigation.created_at >= cutoff
        ).scalar() or 0

        return count

    def _get_last_investigation_for_facility(
        self,
        facility_id: str
    ) -> Optional[Investigation]:
        """
        Get the most recent auto-investigation for a facility.

        Args:
            facility_id: Facility ID to check

        Returns:
            Most recent Investigation or None
        """
        return self.db.query(Investigation).filter(
            Investigation.source == "auto_discovery",
            Investigation.related_facilities.contains(facility_id)
        ).order_by(Investigation.created_at.desc()).first()

    def _has_existing_investigation_for_image(self, content_hash: str) -> bool:
        """
        Check if an image with this hash has already been investigated.

        Args:
            content_hash: SHA256 hash of image content

        Returns:
            True if already investigated
        """
        # Check if any tiger_image with this hash has an associated investigation
        existing = self.db.query(TigerImage).filter(
            TigerImage.content_hash == content_hash,
            TigerImage.discovered_by_investigation_id.isnot(None)
        ).first()

        return existing is not None

    async def should_trigger_investigation(
        self,
        tiger_image: TigerImage,
        facility: Facility,
        detection_confidence: float,
        quality_score: float
    ) -> Tuple[bool, str]:
        """
        Determine if discovered tiger should trigger auto-investigation.

        Checks:
        1. Quality gate
        2. Detection confidence gate
        3. Global rate limit
        4. Per-facility rate limit
        5. Duplicate check

        Args:
            tiger_image: The discovered tiger image
            facility: Associated facility
            detection_confidence: MegaDetector confidence
            quality_score: Image quality score (0-100)

        Returns:
            (should_trigger, reason) tuple
        """
        # Check if auto-investigation is enabled
        auto_config = getattr(self.settings, 'auto_investigation', None)
        if auto_config and not getattr(auto_config, 'enabled', True):
            return (False, "Auto-investigation disabled in settings")

        # 1. Quality gate
        if quality_score < self.MIN_QUALITY_SCORE:
            return (
                False,
                f"Quality {quality_score:.1f} below threshold {self.MIN_QUALITY_SCORE}"
            )

        # 2. Detection confidence gate
        if detection_confidence < self.MIN_DETECTION_CONFIDENCE:
            return (
                False,
                f"Detection confidence {detection_confidence:.2f} below threshold {self.MIN_DETECTION_CONFIDENCE}"
            )

        # 3. Rate limit - global
        recent_auto = self._count_recent_auto_investigations(hours=1)
        if recent_auto >= self.MAX_INVESTIGATIONS_PER_HOUR:
            return (
                False,
                f"Rate limit: {recent_auto} investigations in last hour"
            )

        # 4. Rate limit - per facility
        last_facility_investigation = self._get_last_investigation_for_facility(
            str(facility.facility_id)
        )
        if last_facility_investigation and last_facility_investigation.created_at:
            seconds_since = (
                datetime.utcnow() - last_facility_investigation.created_at
            ).total_seconds()
            if seconds_since < self.MIN_TIME_BETWEEN_FACILITY:
                return (
                    False,
                    f"Facility rate limit: {seconds_since:.0f}s since last (min: {self.MIN_TIME_BETWEEN_FACILITY}s)"
                )

        # 5. Duplicate check - don't investigate same image twice
        if tiger_image.content_hash:
            if self._has_existing_investigation_for_image(tiger_image.content_hash):
                return (False, "Image already investigated")

        return (True, "All criteria met")

    async def trigger_investigation(
        self,
        tiger_image: TigerImage,
        image_bytes: bytes,
        facility: Facility,
        detection_confidence: float,
        quality_score: float = 70.0
    ) -> Optional[Investigation]:
        """
        Create and queue auto-investigation for a discovered tiger.

        This method is FIRE-AND-FORGET - it queues the investigation
        for async background processing and returns immediately.

        Args:
            tiger_image: The discovered tiger image
            image_bytes: Raw image bytes
            facility: Associated facility
            detection_confidence: MegaDetector confidence
            quality_score: Image quality score

        Returns:
            Investigation record if queued, None if criteria not met
        """
        # Check trigger criteria
        should_trigger, reason = await self.should_trigger_investigation(
            tiger_image=tiger_image,
            facility=facility,
            detection_confidence=detection_confidence,
            quality_score=quality_score
        )

        if not should_trigger:
            logger.debug(f"Auto-investigation not triggered: {reason}")
            return None

        logger.info(
            f"[AUTO-TRIGGER] Triggering investigation for tiger at {facility.exhibitor_name}"
        )

        # Create investigation record
        investigation_id = str(uuid4())
        location = f"{facility.city}, {facility.state}" if facility.city else facility.state

        investigation = Investigation(
            investigation_id=investigation_id,
            title=f"Auto-Discovery: Tiger at {facility.exhibitor_name}",
            description=f"Automatically triggered investigation for tiger discovered via continuous crawler at {facility.exhibitor_name}.",
            created_by="system",  # System user for auto-investigations
            status=InvestigationStatus.active.value,
            priority=self._determine_priority(detection_confidence, quality_score),
            source="auto_discovery",  # Mark as auto-discovery
            started_at=datetime.utcnow(),
            related_facilities=[str(facility.facility_id)],
            tags=["auto_discovery", "continuous_crawler", "pending_review"]
        )

        self.db.add(investigation)
        self.db.commit()

        # Build context for investigation workflow
        context = {
            "location": location,
            "notes": f"Auto-triggered from facility crawl: {facility.exhibitor_name}",
            "source": "auto_discovery",
            "source_tiger_id": str(tiger_image.tiger_id) if tiger_image.tiger_id else None,
            "source_image_id": str(tiger_image.image_id),
            "facility_id": str(facility.facility_id),
            "facility_name": facility.exhibitor_name,
            "use_deep_research": True,  # Use DuckDuckGo deep research
            "detection_confidence": detection_confidence,
            "quality_score": quality_score
        }

        # Queue for async background processing - DOES NOT BLOCK
        try:
            from backend.services.investigation2_task_runner import queue_investigation

            queue_investigation(
                investigation_id=UUID(investigation_id),
                image_bytes=image_bytes,
                context=context
            )

            logger.info(
                f"[AUTO-TRIGGER] Investigation {investigation_id[:8]} queued for "
                f"{facility.exhibitor_name} (confidence={detection_confidence:.2f})"
            )

        except Exception as e:
            logger.error(f"Failed to queue auto-investigation: {e}")
            # Update investigation status to failed
            investigation.status = InvestigationStatus.cancelled.value
            self.db.commit()
            return None

        return investigation

    def _determine_priority(
        self,
        detection_confidence: float,
        quality_score: float
    ) -> str:
        """
        Determine investigation priority based on confidence and quality.

        Args:
            detection_confidence: MegaDetector confidence
            quality_score: Image quality score

        Returns:
            Priority string: 'high', 'medium', or 'low'
        """
        combined_score = (detection_confidence * 100 + quality_score) / 2

        if combined_score >= 90:
            return Priority.high.value
        elif combined_score >= 75:
            return Priority.medium.value
        else:
            return Priority.low.value

    async def add_to_verification_queue(
        self,
        entity_type: str,
        entity_id: str,
        source: str,
        priority: str = "medium",
        notes: Optional[str] = None
    ) -> VerificationQueue:
        """
        Add an entity to the verification queue for human review.

        All discovered tigers (auto or user-uploaded) go to pending review.

        Args:
            entity_type: 'tiger', 'facility', etc.
            entity_id: The entity's ID
            source: 'auto_discovery' or 'user_upload'
            priority: 'high', 'medium', 'low'
            notes: Optional notes about the entity

        Returns:
            Created VerificationQueue entry
        """
        verification = VerificationQueue(
            queue_id=str(uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            priority=priority,
            requires_human_review=True,
            status=VerificationStatus.pending.value,  # Always pending per user requirement
            source=source,
            review_notes=notes,
            created_at=datetime.utcnow()
        )

        self.db.add(verification)
        self.db.commit()

        logger.info(
            f"[VERIFICATION QUEUE] Added {entity_type} {entity_id[:8]} "
            f"(source={source}, priority={priority})"
        )

        return verification


# Convenience function
def get_investigation_trigger_service(db_session: Session) -> InvestigationTriggerService:
    """Create and return an InvestigationTriggerService instance."""
    return InvestigationTriggerService(db_session)
