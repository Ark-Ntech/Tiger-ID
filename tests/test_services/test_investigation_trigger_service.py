"""
Comprehensive unit tests for InvestigationTriggerService.

Tests cover:
1. Quality gate enforcement (MIN_QUALITY_SCORE = 60.0)
2. Detection confidence gate enforcement (MIN_DETECTION_CONFIDENCE = 0.85)
3. Global rate limiting (MAX_INVESTIGATIONS_PER_HOUR = 5)
4. Per-facility rate limiting (MIN_TIME_BETWEEN_FACILITY = 3600s)
5. Duplicate image prevention (content_hash tracking)
6. Investigation record creation with source="auto_discovery"
7. Verification queue entry creation with status="pending"
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from backend.services.investigation_trigger_service import (
    InvestigationTriggerService,
    get_investigation_trigger_service
)
from backend.database.models import (
    Tiger, TigerImage, Facility, Investigation, VerificationQueue,
    InvestigationStatus, Priority, VerificationStatus
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings object with auto_investigation config disabled."""
    settings = Mock()
    # Disable auto_investigation config to use default values
    settings.auto_investigation = None
    return settings


@pytest.fixture
def trigger_service(db_session, mock_settings):
    """Create InvestigationTriggerService with mocked settings."""
    with patch('backend.services.investigation_trigger_service.get_settings', return_value=mock_settings):
        service = InvestigationTriggerService(db_session)
    return service


@pytest.fixture
def sample_facility(db_session):
    """Create a sample facility for testing."""
    facility = Facility(
        facility_id=str(uuid4()),
        exhibitor_name="Test Zoo",
        state="CA",
        city="Los Angeles",
        tiger_count=5,
        created_at=datetime.utcnow()
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility


@pytest.fixture
def sample_tiger(db_session, sample_facility):
    """Create a sample tiger for testing."""
    tiger = Tiger(
        tiger_id=str(uuid4()),
        name="Test Tiger",
        origin_facility_id=sample_facility.facility_id,
        status="active",
        created_at=datetime.utcnow()
    )
    db_session.add(tiger)
    db_session.commit()
    db_session.refresh(tiger)
    return tiger


@pytest.fixture
def sample_tiger_image(db_session, sample_tiger):
    """Create a sample tiger image for testing."""
    image = TigerImage(
        image_id=str(uuid4()),
        tiger_id=sample_tiger.tiger_id,
        image_path="/path/to/test.jpg",
        content_hash="abc123def456",
        quality_score=75.0,
        verified=False,
        created_at=datetime.utcnow()
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)
    return image


# ============================================================================
# Test Cases
# ============================================================================

class TestQualityGate:
    """Tests for MIN_QUALITY_SCORE (60.0) enforcement."""

    @pytest.mark.asyncio
    async def test_should_trigger_quality_gate_blocks_low_quality(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Images below MIN_QUALITY_SCORE (60.0) should not trigger investigations."""
        # Test with quality_score = 59.0 (below threshold of 60.0)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,  # High confidence
            quality_score=59.0  # Below threshold
        )

        assert should_trigger is False
        assert "Quality" in reason
        assert "60.0" in reason
        assert "59.0" in reason

    @pytest.mark.asyncio
    async def test_should_trigger_quality_gate_allows_minimum_quality(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Images at exactly MIN_QUALITY_SCORE (60.0) should pass quality gate."""
        # Test with quality_score = 60.0 (exactly at threshold)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,  # High confidence
            quality_score=60.0  # Exactly at threshold
        )

        # Should pass quality gate (may fail on other criteria)
        if not should_trigger:
            assert "Quality" not in reason

    @pytest.mark.asyncio
    async def test_should_trigger_quality_gate_allows_high_quality(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Images above MIN_QUALITY_SCORE should pass quality gate."""
        # Test with quality_score = 85.0 (well above threshold)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=85.0  # Well above threshold
        )

        # Should pass quality gate (may fail on other criteria)
        if not should_trigger:
            assert "Quality" not in reason


class TestConfidenceGate:
    """Tests for MIN_DETECTION_CONFIDENCE (0.85) enforcement."""

    @pytest.mark.asyncio
    async def test_should_trigger_confidence_gate_blocks_low_confidence(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Detections below MIN_DETECTION_CONFIDENCE (0.85) should not trigger."""
        # Test with detection_confidence = 0.84 (below threshold of 0.85)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.84,  # Below threshold
            quality_score=75.0  # Good quality
        )

        assert should_trigger is False
        assert "Detection confidence" in reason
        assert "0.85" in reason
        assert "0.84" in reason

    @pytest.mark.asyncio
    async def test_should_trigger_confidence_gate_allows_minimum_confidence(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Detections at exactly MIN_DETECTION_CONFIDENCE (0.85) should pass."""
        # Test with detection_confidence = 0.85 (exactly at threshold)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.85,  # Exactly at threshold
            quality_score=75.0
        )

        # Should pass confidence gate (may fail on other criteria)
        if not should_trigger:
            assert "Detection confidence" not in reason

    @pytest.mark.asyncio
    async def test_should_trigger_confidence_gate_allows_high_confidence(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Detections with high confidence should pass confidence gate."""
        # Test with detection_confidence = 0.98 (well above threshold)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.98,
            quality_score=75.0
        )

        # Should pass confidence gate (may fail on other criteria)
        if not should_trigger:
            assert "Detection confidence" not in reason


class TestGlobalRateLimiting:
    """Tests for MAX_INVESTIGATIONS_PER_HOUR (5) enforcement."""

    @pytest.mark.asyncio
    async def test_rate_limiting_global_blocks_when_exceeded(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should block when MAX_INVESTIGATIONS_PER_HOUR (5) is exceeded."""
        # Create 5 auto-discovery investigations in the last 30 minutes
        # Use recent timestamps to ensure they're well within the 1-hour window
        now = datetime.utcnow()
        for i in range(5):
            investigation = Investigation(
                investigation_id=str(uuid4()),
                title=f"Auto Investigation {i}",
                created_by="system",
                status=InvestigationStatus.active.value,
                source="auto_discovery",
                created_at=now - timedelta(minutes=30 - i * 5)  # 30, 25, 20, 15, 10 minutes ago
            )
            db_session.add(investigation)
        db_session.commit()

        # Attempt to trigger another investigation
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        assert should_trigger is False
        assert "Rate limit" in reason or "5" in reason  # Message may vary
        assert "investigation" in reason.lower() or "limit" in reason.lower()

    @pytest.mark.asyncio
    async def test_rate_limiting_global_allows_when_under_limit(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should allow when under MAX_INVESTIGATIONS_PER_HOUR limit."""
        # Create only 4 auto-discovery investigations (under limit of 5)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        for i in range(4):
            investigation = Investigation(
                investigation_id=str(uuid4()),
                title=f"Auto Investigation {i}",
                created_by="system",
                status=InvestigationStatus.active.value,
                source="auto_discovery",
                created_at=cutoff + timedelta(minutes=i * 10)
            )
            db_session.add(investigation)
        db_session.commit()

        # Should pass global rate limit
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        # Should pass global rate limit (may fail on other criteria)
        if not should_trigger:
            assert "Rate limit" not in reason or "hour" not in reason

    @pytest.mark.asyncio
    async def test_rate_limiting_global_ignores_old_investigations(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should ignore investigations older than 1 hour."""
        # Create 5 auto-discovery investigations older than 1 hour
        old_time = datetime.utcnow() - timedelta(hours=2)
        for i in range(5):
            investigation = Investigation(
                investigation_id=str(uuid4()),
                title=f"Old Investigation {i}",
                created_by="system",
                status=InvestigationStatus.active.value,
                source="auto_discovery",
                created_at=old_time
            )
            db_session.add(investigation)
        db_session.commit()

        # Should not count old investigations
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        # Should pass global rate limit (may fail on other criteria)
        if not should_trigger:
            assert "Rate limit" not in reason or "hour" not in reason

    @pytest.mark.asyncio
    async def test_rate_limiting_global_ignores_user_uploaded_investigations(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should only count auto_discovery investigations, not user_upload."""
        # Create 5 user_upload investigations (should not count)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        for i in range(5):
            investigation = Investigation(
                investigation_id=str(uuid4()),
                title=f"User Investigation {i}",
                created_by="user123",
                status=InvestigationStatus.active.value,
                source="user_upload",  # Not auto_discovery
                created_at=cutoff + timedelta(minutes=i * 10)
            )
            db_session.add(investigation)
        db_session.commit()

        # Should not count user_upload investigations
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        # Should pass global rate limit (may fail on other criteria)
        if not should_trigger:
            assert "Rate limit" not in reason or "hour" not in reason


class TestPerFacilityRateLimiting:
    """Tests for MIN_TIME_BETWEEN_FACILITY (3600s) enforcement."""

    @pytest.mark.asyncio
    async def test_rate_limiting_per_facility_blocks_when_too_soon(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should block when investigating same facility within 3600 seconds."""
        # Create an auto-discovery investigation for this facility 30 minutes ago
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        investigation = Investigation(
            investigation_id=str(uuid4()),
            title="Recent Facility Investigation",
            created_by="system",
            status=InvestigationStatus.active.value,
            source="auto_discovery",
            related_facilities=[str(sample_facility.facility_id)],
            created_at=recent_time
        )
        db_session.add(investigation)
        db_session.commit()

        # Attempt to trigger another investigation for same facility
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        assert should_trigger is False
        assert "Facility rate limit" in reason
        assert "3600" in reason or "1 hour" in reason.lower()

    @pytest.mark.asyncio
    async def test_rate_limiting_per_facility_allows_after_interval(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should allow when MIN_TIME_BETWEEN_FACILITY has elapsed."""
        # Create an auto-discovery investigation for this facility 2 hours ago
        old_time = datetime.utcnow() - timedelta(hours=2)
        investigation = Investigation(
            investigation_id=str(uuid4()),
            title="Old Facility Investigation",
            created_by="system",
            status=InvestigationStatus.active.value,
            source="auto_discovery",
            related_facilities=[str(sample_facility.facility_id)],
            created_at=old_time
        )
        db_session.add(investigation)
        db_session.commit()

        # Should allow (enough time has passed)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        # Should pass facility rate limit (may fail on other criteria)
        if not should_trigger:
            assert "Facility rate limit" not in reason

    @pytest.mark.asyncio
    async def test_rate_limiting_per_facility_allows_different_facility(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should allow investigations for different facilities."""
        # Create an investigation for a different facility
        other_facility_id = str(uuid4())
        recent_time = datetime.utcnow() - timedelta(minutes=10)
        investigation = Investigation(
            investigation_id=str(uuid4()),
            title="Other Facility Investigation",
            created_by="system",
            status=InvestigationStatus.active.value,
            source="auto_discovery",
            related_facilities=[other_facility_id],  # Different facility
            created_at=recent_time
        )
        db_session.add(investigation)
        db_session.commit()

        # Should allow (different facility)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        # Should pass facility rate limit (may fail on other criteria)
        if not should_trigger:
            assert "Facility rate limit" not in reason


class TestDuplicatePrevention:
    """Tests for duplicate image prevention via content_hash."""

    @pytest.mark.asyncio
    async def test_duplicate_image_prevention_blocks_existing_hash(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should not re-investigate images with existing content_hash."""
        # Mark the image as already investigated
        sample_tiger_image.discovered_by_investigation_id = str(uuid4())
        db_session.commit()

        # Attempt to trigger investigation for same image
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        assert should_trigger is False
        assert "already investigated" in reason.lower()

    @pytest.mark.asyncio
    async def test_duplicate_image_prevention_allows_new_hash(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should allow investigation of new content_hash."""
        # Ensure image has not been investigated
        sample_tiger_image.discovered_by_investigation_id = None
        db_session.commit()

        # Should allow (new image)
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        # Should pass duplicate check (may fail on other criteria)
        if not should_trigger:
            assert "already investigated" not in reason.lower()

    @pytest.mark.asyncio
    async def test_duplicate_image_prevention_handles_no_hash(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should handle images without content_hash gracefully."""
        # Remove content_hash
        sample_tiger_image.content_hash = None
        db_session.commit()

        # Should not crash and should pass duplicate check
        should_trigger, reason = await trigger_service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=75.0
        )

        # Should pass duplicate check (may fail on other criteria)
        if not should_trigger:
            assert "already investigated" not in reason.lower()


class TestTriggerInvestigation:
    """Tests for trigger_investigation method."""

    @pytest.mark.asyncio
    async def test_trigger_investigation_creates_record(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should create Investigation record with source='auto_discovery'."""
        # Mock queue_investigation to prevent actual queueing
        with patch('backend.services.investigation2_task_runner.queue_investigation') as mock_queue:
            image_bytes = b"fake image data"

            investigation = await trigger_service.trigger_investigation(
                tiger_image=sample_tiger_image,
                image_bytes=image_bytes,
                facility=sample_facility,
                detection_confidence=0.95,
                quality_score=75.0
            )

            assert investigation is not None
            assert investigation.source == "auto_discovery"
            assert investigation.created_by == "system"
            assert investigation.status == InvestigationStatus.active.value
            assert investigation.investigation_id is not None
            assert sample_facility.exhibitor_name in investigation.title
            assert str(sample_facility.facility_id) in investigation.related_facilities

            # Verify investigation was saved to database
            db_investigation = db_session.query(Investigation).filter_by(
                investigation_id=investigation.investigation_id
            ).first()
            assert db_investigation is not None
            assert db_investigation.source == "auto_discovery"

    @pytest.mark.asyncio
    async def test_trigger_investigation_queues_task(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Should call queue_investigation with correct parameters."""
        with patch('backend.services.investigation2_task_runner.queue_investigation') as mock_queue:
            image_bytes = b"fake image data"

            investigation = await trigger_service.trigger_investigation(
                tiger_image=sample_tiger_image,
                image_bytes=image_bytes,
                facility=sample_facility,
                detection_confidence=0.95,
                quality_score=75.0
            )

            # Verify queue_investigation was called
            assert mock_queue.called
            call_args = mock_queue.call_args

            # Check arguments
            assert 'investigation_id' in call_args.kwargs or len(call_args.args) > 0
            assert 'image_bytes' in call_args.kwargs or len(call_args.args) > 1
            assert 'context' in call_args.kwargs or len(call_args.args) > 2

            # Check context contains expected keys
            context = call_args.kwargs.get('context', call_args.args[2] if len(call_args.args) > 2 else {})
            assert context['source'] == "auto_discovery"
            assert context['use_deep_research'] is True
            assert context['facility_id'] == str(sample_facility.facility_id)

    @pytest.mark.asyncio
    async def test_trigger_investigation_returns_none_when_blocked(
        self, trigger_service, sample_tiger_image, sample_facility
    ):
        """Should return None when trigger criteria not met."""
        # Use low quality to fail quality gate
        investigation = await trigger_service.trigger_investigation(
            tiger_image=sample_tiger_image,
            image_bytes=b"fake image data",
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=50.0  # Below threshold
        )

        assert investigation is None

    @pytest.mark.asyncio
    async def test_trigger_investigation_handles_queue_failure(
        self, trigger_service, db_session, sample_tiger_image, sample_facility
    ):
        """Should mark investigation as cancelled if queueing fails."""
        with patch('backend.services.investigation2_task_runner.queue_investigation') as mock_queue:
            mock_queue.side_effect = Exception("Queue failure")

            investigation = await trigger_service.trigger_investigation(
                tiger_image=sample_tiger_image,
                image_bytes=b"fake image data",
                facility=sample_facility,
                detection_confidence=0.95,
                quality_score=75.0
            )

            # Should return None on queue failure
            assert investigation is None or investigation.status == InvestigationStatus.cancelled.value


class TestPriorityDetermination:
    """Tests for _determine_priority method."""

    def test_determine_priority_high(self, trigger_service):
        """Should return 'high' priority for excellent scores."""
        priority = trigger_service._determine_priority(
            detection_confidence=0.95,
            quality_score=95.0
        )
        assert priority == Priority.high.value

    def test_determine_priority_medium(self, trigger_service):
        """Should return 'medium' priority for good scores."""
        priority = trigger_service._determine_priority(
            detection_confidence=0.85,
            quality_score=75.0
        )
        assert priority == Priority.medium.value

    def test_determine_priority_low(self, trigger_service):
        """Should return 'low' priority for minimal scores."""
        priority = trigger_service._determine_priority(
            detection_confidence=0.85,
            quality_score=60.0
        )
        # Combined score = (0.85 * 100 + 60.0) / 2 = 72.5, should be low
        assert priority == Priority.low.value


class TestVerificationQueue:
    """Tests for add_to_verification_queue method."""

    @pytest.mark.asyncio
    async def test_add_to_verification_queue_creates_entry(
        self, trigger_service, db_session
    ):
        """Should create VerificationQueue entry with status='pending'."""
        entity_id = str(uuid4())

        verification = await trigger_service.add_to_verification_queue(
            entity_type="tiger",
            entity_id=entity_id,
            source="auto_discovery",
            priority="high",
            notes="Test tiger needs review"
        )

        assert verification is not None
        assert verification.entity_type == "tiger"
        assert verification.entity_id == entity_id
        assert verification.source == "auto_discovery"
        assert verification.priority == "high"
        assert verification.status == VerificationStatus.pending.value
        assert verification.requires_human_review is True
        assert verification.review_notes == "Test tiger needs review"

        # Verify saved to database
        db_verification = db_session.query(VerificationQueue).filter_by(
            queue_id=verification.queue_id
        ).first()
        assert db_verification is not None
        assert db_verification.status == VerificationStatus.pending.value

    @pytest.mark.asyncio
    async def test_add_to_verification_queue_defaults_to_pending(
        self, trigger_service, db_session
    ):
        """Should always create entries with status='pending'."""
        verification = await trigger_service.add_to_verification_queue(
            entity_type="facility",
            entity_id=str(uuid4()),
            source="user_upload"
        )

        assert verification.status == VerificationStatus.pending.value
        assert verification.requires_human_review is True

    @pytest.mark.asyncio
    async def test_add_to_verification_queue_handles_optional_params(
        self, trigger_service
    ):
        """Should handle optional priority and notes parameters."""
        # Test without optional parameters
        verification = await trigger_service.add_to_verification_queue(
            entity_type="tiger",
            entity_id=str(uuid4()),
            source="auto_discovery"
        )

        assert verification is not None
        # Default priority should be applied
        assert verification.priority in ["low", "medium", "high"]


class TestConfigurationLoading:
    """Tests for configuration loading from settings."""

    def test_loads_default_values_when_no_config(self, db_session):
        """Should use default values when settings.auto_investigation is None."""
        mock_settings = Mock()
        mock_settings.auto_investigation = None

        with patch('backend.services.investigation_trigger_service.get_settings', return_value=mock_settings):
            service = InvestigationTriggerService(db_session)

        assert service.MIN_QUALITY_SCORE == 60.0
        assert service.MIN_DETECTION_CONFIDENCE == 0.85
        assert service.MAX_INVESTIGATIONS_PER_HOUR == 5
        assert service.MIN_TIME_BETWEEN_FACILITY == 3600

    def test_loads_custom_values_from_config(self, db_session):
        """Should load custom values from settings.auto_investigation."""
        mock_settings = Mock()
        mock_settings.auto_investigation = Mock(
            min_quality_score=70.0,
            min_detection_confidence=0.90,
            max_per_hour=10,
            min_facility_interval_seconds=7200
        )

        with patch('backend.services.investigation_trigger_service.get_settings', return_value=mock_settings):
            service = InvestigationTriggerService(db_session)

        assert service.MIN_QUALITY_SCORE == 70.0
        assert service.MIN_DETECTION_CONFIDENCE == 0.90
        assert service.MAX_INVESTIGATIONS_PER_HOUR == 10
        assert service.MIN_TIME_BETWEEN_FACILITY == 7200

    @pytest.mark.asyncio
    async def test_respects_disabled_flag_in_config(self, db_session, sample_tiger_image, sample_facility):
        """Should block all investigations when auto_investigation.enabled=False."""
        mock_settings = Mock()
        mock_settings.auto_investigation = Mock(enabled=False)

        with patch('backend.services.investigation_trigger_service.get_settings', return_value=mock_settings):
            service = InvestigationTriggerService(db_session)

        should_trigger, reason = await service.should_trigger_investigation(
            tiger_image=sample_tiger_image,
            facility=sample_facility,
            detection_confidence=0.95,
            quality_score=85.0
        )

        assert should_trigger is False
        assert "disabled" in reason.lower()


class TestConvenienceFunction:
    """Tests for get_investigation_trigger_service convenience function."""

    def test_get_investigation_trigger_service(self, db_session):
        """Should create and return InvestigationTriggerService instance."""
        with patch('backend.services.investigation_trigger_service.get_settings'):
            service = get_investigation_trigger_service(db_session)

        assert isinstance(service, InvestigationTriggerService)
        assert service.db == db_session
