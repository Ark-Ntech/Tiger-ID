"""
Unit tests for Investigation2Workflow tiger storage methods.

Tests the following methods:
- _store_investigation_tiger: Store user-uploaded tigers with verification queue integration
- _add_to_verification_queue: Queue entities for human review
- _determine_verification_priority: Calculate verification priority based on context
- _link_investigation_to_source_tiger: Link auto-investigation results back to source tiger
"""

import pytest
import asyncio
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import numpy as np
import hashlib
import json

from backend.agents.investigation2_workflow import Investigation2Workflow, Investigation2State
from backend.database.models import (
    Tiger, TigerImage, VerificationQueue, TigerStatus,
    SideView, VerificationStatus, Priority
)


@pytest.fixture
def mock_db():
    """Mock database session with query support"""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.flush = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def workflow(mock_db):
    """Create workflow instance with mocked database"""
    return Investigation2Workflow(db=mock_db)


@pytest.fixture
def sample_investigation_id():
    """Generate sample investigation ID"""
    return uuid4()


@pytest.fixture
def sample_tiger_id():
    """Generate sample tiger ID"""
    return str(uuid4())


@pytest.fixture
def sample_image_bytes():
    """Create sample tiger image bytes"""
    return b"fake_tiger_image_data_for_testing"


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings dictionary"""
    return {
        "wildlife_tools": np.random.rand(1536).astype(np.float32),
        "cvwc2019": np.random.rand(2048).astype(np.float32),
        "tiger_reid": np.random.rand(2048).astype(np.float32),
        "rapid": np.random.rand(2048).astype(np.float32)
    }


@pytest.fixture
def sample_detected_tigers():
    """Create sample detected tigers list"""
    return [
        {
            "bbox": [100, 100, 300, 400],
            "confidence": 0.95,
            "crop": b"cropped_tiger_data"
        }
    ]


@pytest.fixture
def sample_context():
    """Create sample investigation context"""
    return {
        "source": "user_upload",
        "location": "Texas Wildlife Sanctuary",
        "date": "2025-01-15",
        "notes": "Tiger spotted in enclosure",
        "image_quality": {
            "overall_score": 0.87,
            "blur_score": 0.92,
            "resolution": "1920x1080"
        }
    }


class TestStoreInvestigationTiger:
    """Tests for _store_investigation_tiger method"""

    @pytest.mark.asyncio
    async def test_store_investigation_tiger_creates_record(
        self,
        workflow,
        mock_db,
        sample_image_bytes,
        sample_embeddings,
        sample_investigation_id,
        sample_detected_tigers,
        sample_context
    ):
        """
        Test that _store_investigation_tiger creates Tiger and TigerImage records correctly.

        Validates:
        - Tiger record created with correct attributes
        - TigerImage record created with embeddings
        - Database operations called properly
        - Returns tiger_id
        """
        # Mock no existing strong matches
        existing_matches = {
            "wildlife_tools": [{"similarity": 0.75, "tiger_name": "Tiger A"}],
            "cvwc2019": [{"similarity": 0.68, "tiger_name": "Tiger B"}]
        }

        # Mock no existing image with same hash
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('backend.agents.investigation2_workflow.store_embedding') as mock_store_embedding:
            result = await workflow._store_investigation_tiger(
                image_bytes=sample_image_bytes,
                embeddings=sample_embeddings,
                investigation_id=sample_investigation_id,
                location="Texas Wildlife Sanctuary",
                detected_tigers=sample_detected_tigers,
                existing_matches=existing_matches,
                context=sample_context
            )

        # Verify tiger_id returned
        assert result is not None
        assert isinstance(result, str)

        # Verify database add called for Tiger and TigerImage
        assert mock_db.add.call_count == 2

        # Verify flush and commit called
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify Tiger record created with correct attributes
        tiger_call = mock_db.add.call_args_list[0]
        tiger = tiger_call[0][0]
        assert isinstance(tiger, Tiger)
        assert tiger.name.startswith("Investigation Tiger")
        assert tiger.last_seen_location == "Texas Wildlife Sanctuary"
        assert tiger.status == TigerStatus.active.value
        assert tiger.is_reference is False
        assert tiger.discovered_by_investigation_id == str(sample_investigation_id)

        # Verify TigerImage record created with correct attributes
        image_call = mock_db.add.call_args_list[1]
        image = image_call[0][0]
        assert isinstance(image, TigerImage)
        assert image.tiger_id == tiger.tiger_id
        assert image.verified is False
        assert image.is_reference is False
        assert image.discovered_by_investigation_id == str(sample_investigation_id)

        # Verify content hash computed
        expected_hash = hashlib.sha256(sample_image_bytes).hexdigest()
        assert image.content_hash == expected_hash

        # Verify quality score set from context
        assert image.quality_score == 87.0  # 0.87 * 100

        # Verify embedding stored
        mock_store_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_investigation_tiger_skips_strong_match(
        self,
        workflow,
        mock_db,
        sample_image_bytes,
        sample_embeddings,
        sample_investigation_id,
        sample_detected_tigers,
        sample_context
    ):
        """
        Test that _store_investigation_tiger skips storage when strong match (>90%) exists.

        Validates:
        - Returns None when similarity > 0.90
        - No database operations performed
        - Logs appropriate message
        """
        # Mock strong match found
        existing_matches = {
            "wildlife_tools": [
                {"similarity": 0.95, "tiger_name": "Tiger A", "tiger_id": "tiger-123"}
            ],
            "cvwc2019": [
                {"similarity": 0.88, "tiger_name": "Tiger B"}
            ]
        }

        with patch('backend.agents.investigation2_workflow.logger') as mock_logger:
            result = await workflow._store_investigation_tiger(
                image_bytes=sample_image_bytes,
                embeddings=sample_embeddings,
                investigation_id=sample_investigation_id,
                location="Texas Wildlife Sanctuary",
                detected_tigers=sample_detected_tigers,
                existing_matches=existing_matches,
                context=sample_context
            )

        # Verify returns None
        assert result is None

        # Verify no database operations
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

        # Verify logged skip message
        mock_logger.info.assert_called()
        log_msg = mock_logger.info.call_args[0][0]
        assert "Skipping - strong match found" in log_msg
        assert "Tiger A" in log_msg

    @pytest.mark.asyncio
    async def test_store_investigation_tiger_skips_duplicate_hash(
        self,
        workflow,
        mock_db,
        sample_image_bytes,
        sample_embeddings,
        sample_investigation_id,
        sample_detected_tigers,
        sample_context
    ):
        """
        Test that _store_investigation_tiger skips storage when duplicate content_hash exists.

        Validates:
        - Returns existing tiger_id when hash matches
        - No new records created
        - Logs appropriate message
        """
        # Mock no strong match
        existing_matches = {
            "wildlife_tools": [{"similarity": 0.75, "tiger_name": "Tiger A"}]
        }

        # Mock existing image with same hash
        existing_tiger_id = str(uuid4())
        existing_image = Mock(spec=TigerImage)
        existing_image.image_id = str(uuid4())
        existing_image.tiger_id = existing_tiger_id
        existing_image.content_hash = hashlib.sha256(sample_image_bytes).hexdigest()

        mock_db.query.return_value.filter.return_value.first.return_value = existing_image

        with patch('backend.agents.investigation2_workflow.logger') as mock_logger:
            result = await workflow._store_investigation_tiger(
                image_bytes=sample_image_bytes,
                embeddings=sample_embeddings,
                investigation_id=sample_investigation_id,
                location="Texas Wildlife Sanctuary",
                detected_tigers=sample_detected_tigers,
                existing_matches=existing_matches,
                context=sample_context
            )

        # Verify returns existing tiger_id
        assert result == existing_tiger_id

        # Verify no new records created (add not called)
        mock_db.add.assert_not_called()

        # Verify logged message
        mock_logger.info.assert_called()
        log_msg = mock_logger.info.call_args[0][0]
        assert "Image already exists" in log_msg

    @pytest.mark.asyncio
    async def test_store_investigation_tiger_no_embeddings(
        self,
        workflow,
        mock_db,
        sample_image_bytes,
        sample_investigation_id,
        sample_detected_tigers,
        sample_context
    ):
        """
        Test that _store_investigation_tiger skips storage when no embeddings available.

        Validates:
        - Returns None when embeddings empty
        - Logs warning message
        """
        # Empty embeddings
        embeddings = {}
        existing_matches = {}

        with patch('backend.agents.investigation2_workflow.logger') as mock_logger:
            result = await workflow._store_investigation_tiger(
                image_bytes=sample_image_bytes,
                embeddings=embeddings,
                investigation_id=sample_investigation_id,
                location="Texas Wildlife Sanctuary",
                detected_tigers=sample_detected_tigers,
                existing_matches=existing_matches,
                context=sample_context
            )

        # Verify returns None
        assert result is None

        # Verify logged warning
        mock_logger.warning.assert_called()
        log_msg = mock_logger.warning.call_args[0][0]
        assert "No embeddings available" in log_msg

    @pytest.mark.asyncio
    async def test_store_investigation_tiger_no_database(
        self,
        sample_image_bytes,
        sample_embeddings,
        sample_investigation_id,
        sample_detected_tigers,
        sample_context
    ):
        """
        Test that _store_investigation_tiger handles missing database gracefully.

        Validates:
        - Returns None when no database session
        - Logs warning
        """
        # Create workflow without database
        workflow = Investigation2Workflow(db=None)

        with patch('backend.agents.investigation2_workflow.logger') as mock_logger:
            result = await workflow._store_investigation_tiger(
                image_bytes=sample_image_bytes,
                embeddings=sample_embeddings,
                investigation_id=sample_investigation_id,
                location="Texas Wildlife Sanctuary",
                detected_tigers=sample_detected_tigers,
                existing_matches={},
                context=sample_context
            )

        # Verify returns None
        assert result is None

        # Verify logged warning
        mock_logger.warning.assert_called()
        log_msg = mock_logger.warning.call_args[0][0]
        assert "No database session" in log_msg


class TestAddToVerificationQueue:
    """Tests for _add_to_verification_queue method"""

    @pytest.mark.asyncio
    async def test_add_to_verification_queue_creates_entry(
        self,
        workflow,
        mock_db,
        sample_tiger_id,
        sample_investigation_id
    ):
        """
        Test that _add_to_verification_queue creates VerificationQueue entry correctly.

        Validates:
        - VerificationQueue entry created with correct attributes
        - status set to "pending"
        - requires_human_review set to True
        - Returns queue_id
        """
        # Mock no existing queue entry
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await workflow._add_to_verification_queue(
            entity_type="tiger",
            entity_id=sample_tiger_id,
            investigation_id=sample_investigation_id,
            source="user_upload",
            priority="medium",
            notes="User uploaded tiger, needs verification"
        )

        # Verify queue_id returned
        assert result is not None
        assert isinstance(result, str)

        # Verify database add called
        mock_db.add.assert_called_once()

        # Verify commit called
        mock_db.commit.assert_called_once()

        # Verify VerificationQueue entry created
        queue_call = mock_db.add.call_args[0]
        queue_entry = queue_call[0]
        assert isinstance(queue_entry, VerificationQueue)
        assert queue_entry.entity_type == "tiger"
        assert queue_entry.entity_id == sample_tiger_id
        assert queue_entry.priority == "medium"
        assert queue_entry.requires_human_review is True
        assert queue_entry.status == VerificationStatus.pending.value
        assert queue_entry.source == "user_upload"
        assert queue_entry.investigation_id == str(sample_investigation_id)
        assert queue_entry.review_notes == "User uploaded tiger, needs verification"

    @pytest.mark.asyncio
    async def test_add_to_verification_queue_skips_existing(
        self,
        workflow,
        mock_db,
        sample_tiger_id,
        sample_investigation_id
    ):
        """
        Test that _add_to_verification_queue skips creating entry for existing entity.

        Validates:
        - Returns existing queue_id when entity already in queue
        - No new record created
        - Logs appropriate message
        """
        # Mock existing queue entry
        existing_queue_id = str(uuid4())
        existing_entry = Mock(spec=VerificationQueue)
        existing_entry.queue_id = existing_queue_id
        existing_entry.entity_type = "tiger"
        existing_entry.entity_id = sample_tiger_id

        mock_db.query.return_value.filter.return_value.first.return_value = existing_entry

        with patch('backend.agents.investigation2_workflow.logger') as mock_logger:
            result = await workflow._add_to_verification_queue(
                entity_type="tiger",
                entity_id=sample_tiger_id,
                investigation_id=sample_investigation_id,
                source="user_upload",
                priority="medium"
            )

        # Verify returns existing queue_id
        assert result == existing_queue_id

        # Verify no new record created
        mock_db.add.assert_not_called()

        # Verify logged message
        mock_logger.info.assert_called()
        log_msg = mock_logger.info.call_args[0][0]
        assert "already in queue" in log_msg

    @pytest.mark.asyncio
    async def test_add_to_verification_queue_no_database(
        self,
        sample_tiger_id,
        sample_investigation_id
    ):
        """
        Test that _add_to_verification_queue handles missing database gracefully.

        Validates:
        - Returns None when no database session
        """
        # Create workflow without database
        workflow = Investigation2Workflow(db=None)

        result = await workflow._add_to_verification_queue(
            entity_type="tiger",
            entity_id=sample_tiger_id,
            investigation_id=sample_investigation_id,
            source="user_upload",
            priority="medium"
        )

        # Verify returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_add_to_verification_queue_different_priorities(
        self,
        workflow,
        mock_db,
        sample_tiger_id,
        sample_investigation_id
    ):
        """
        Test that _add_to_verification_queue handles different priority levels.

        Validates:
        - "high", "medium", "low" priorities all work correctly
        """
        # Mock no existing queue entry
        mock_db.query.return_value.filter.return_value.first.return_value = None

        for priority in ["high", "medium", "low"]:
            mock_db.reset_mock()

            result = await workflow._add_to_verification_queue(
                entity_type="tiger",
                entity_id=sample_tiger_id,
                investigation_id=sample_investigation_id,
                source="user_upload",
                priority=priority
            )

            # Verify queue entry created with correct priority
            queue_entry = mock_db.add.call_args[0][0]
            assert queue_entry.priority == priority


class TestDetermineVerificationPriority:
    """Tests for _determine_verification_priority method"""

    def test_determine_verification_priority_user_upload(self, workflow):
        """
        Test that _determine_verification_priority returns "medium" for user uploads.

        Validates:
        - User uploads always get "medium" priority regardless of confidence
        """
        state: Investigation2State = {
            "investigation_id": str(uuid4()),
            "uploaded_image": b"fake_image",
            "image_path": None,
            "context": {
                "source": "user_upload",
                "location": "Texas"
            },
            "detected_tigers": [
                {"confidence": 0.99, "bbox": [0, 0, 100, 100]}
            ],
            "reverse_search_results": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "omnivinci_comparison": None,
            "report": None,
            "errors": [],
            "phase": "complete",
            "status": "completed"
        }

        priority = workflow._determine_verification_priority(state)

        assert priority == "medium"

    def test_determine_verification_priority_auto_discovery_high(self, workflow):
        """
        Test that _determine_verification_priority returns "high" for high-confidence auto-discoveries.

        Validates:
        - Auto-discoveries with avg confidence >= 0.95 get "high" priority
        """
        state: Investigation2State = {
            "investigation_id": str(uuid4()),
            "uploaded_image": b"fake_image",
            "image_path": None,
            "context": {
                "source": "auto_discovery",
                "location": "Texas"
            },
            "detected_tigers": [
                {"confidence": 0.97, "bbox": [0, 0, 100, 100]},
                {"confidence": 0.96, "bbox": [100, 0, 200, 100]}
            ],
            "reverse_search_results": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "omnivinci_comparison": None,
            "report": None,
            "errors": [],
            "phase": "complete",
            "status": "completed"
        }

        priority = workflow._determine_verification_priority(state)

        assert priority == "high"

    def test_determine_verification_priority_auto_discovery_medium(self, workflow):
        """
        Test that _determine_verification_priority returns "medium" for medium-confidence auto-discoveries.

        Validates:
        - Auto-discoveries with 0.85 <= avg confidence < 0.95 get "medium" priority
        """
        state: Investigation2State = {
            "investigation_id": str(uuid4()),
            "uploaded_image": b"fake_image",
            "image_path": None,
            "context": {
                "source": "auto_discovery",
                "location": "Texas"
            },
            "detected_tigers": [
                {"confidence": 0.90, "bbox": [0, 0, 100, 100]},
                {"confidence": 0.88, "bbox": [100, 0, 200, 100]}
            ],
            "reverse_search_results": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "omnivinci_comparison": None,
            "report": None,
            "errors": [],
            "phase": "complete",
            "status": "completed"
        }

        priority = workflow._determine_verification_priority(state)

        assert priority == "medium"

    def test_determine_verification_priority_auto_discovery_low(self, workflow):
        """
        Test that _determine_verification_priority returns "low" for low-confidence auto-discoveries.

        Validates:
        - Auto-discoveries with avg confidence < 0.85 get "low" priority
        """
        state: Investigation2State = {
            "investigation_id": str(uuid4()),
            "uploaded_image": b"fake_image",
            "image_path": None,
            "context": {
                "source": "auto_discovery",
                "location": "Texas"
            },
            "detected_tigers": [
                {"confidence": 0.75, "bbox": [0, 0, 100, 100]},
                {"confidence": 0.70, "bbox": [100, 0, 200, 100]}
            ],
            "reverse_search_results": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "omnivinci_comparison": None,
            "report": None,
            "errors": [],
            "phase": "complete",
            "status": "completed"
        }

        priority = workflow._determine_verification_priority(state)

        assert priority == "low"

    def test_determine_verification_priority_no_detected_tigers(self, workflow):
        """
        Test that _determine_verification_priority handles empty detected_tigers list.

        Validates:
        - Returns "low" when no tigers detected (auto-discovery)
        - Returns "medium" for user uploads even with no detections
        """
        # Auto-discovery with no detections
        state_auto: Investigation2State = {
            "investigation_id": str(uuid4()),
            "uploaded_image": b"fake_image",
            "image_path": None,
            "context": {
                "source": "auto_discovery",
                "location": "Texas"
            },
            "detected_tigers": [],
            "reverse_search_results": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "omnivinci_comparison": None,
            "report": None,
            "errors": [],
            "phase": "complete",
            "status": "completed"
        }

        priority_auto = workflow._determine_verification_priority(state_auto)
        assert priority_auto == "low"

        # User upload with no detections
        state_user: Investigation2State = {
            "investigation_id": str(uuid4()),
            "uploaded_image": b"fake_image",
            "image_path": None,
            "context": {
                "source": "user_upload",
                "location": "Texas"
            },
            "detected_tigers": [],
            "reverse_search_results": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "omnivinci_comparison": None,
            "report": None,
            "errors": [],
            "phase": "complete",
            "status": "completed"
        }

        priority_user = workflow._determine_verification_priority(state_user)
        assert priority_user == "medium"


class TestLinkInvestigationToSourceTiger:
    """Tests for _link_investigation_to_source_tiger method"""

    @pytest.mark.asyncio
    async def test_link_investigation_to_source_tiger(
        self,
        workflow,
        mock_db,
        sample_investigation_id,
        sample_tiger_id
    ):
        """
        Test that _link_investigation_to_source_tiger updates source tiger correctly.

        Validates:
        - Source tiger notes updated with investigation reference
        - "investigated" tag added to tiger
        - Database commit called
        """
        # Create a simple class to track attribute updates (Mock doesn't persist assignments)
        class MockTiger:
            def __init__(self):
                self.tiger_id = sample_tiger_id
                self.tags = ["auto_discovery", "pending_review"]  # List format, not JSON
                self.notes = "Initial notes about this tiger"

        source_tiger = MockTiger()
        mock_db.query.return_value.filter.return_value.first.return_value = source_tiger

        matches = {
            "wildlife_tools": [
                {"similarity": 0.85, "tiger_name": "Tiger A"}
            ]
        }

        report = {
            "confidence": "high",
            "summary": "Strong match found"
        }

        with patch('backend.agents.investigation2_workflow.logger') as mock_logger:
            await workflow._link_investigation_to_source_tiger(
                investigation_id=sample_investigation_id,
                source_tiger_id=sample_tiger_id,
                matches=matches,
                report=report
            )

        # Verify tiger tags updated (tags is a list in the implementation)
        assert "investigated" in source_tiger.tags
        assert "auto_discovery" in source_tiger.tags

        # Verify tiger notes updated
        assert source_tiger.notes is not None
        assert f"[Investigation {str(sample_investigation_id)[:8]}]" in source_tiger.notes
        assert "Confidence: high" in source_tiger.notes
        assert "Initial notes about this tiger" in source_tiger.notes

        # Verify commit called
        mock_db.commit.assert_called_once()

        # Verify logged message
        mock_logger.info.assert_called()
        log_msg = mock_logger.info.call_args[0][0]
        assert "Linked investigation" in log_msg

    @pytest.mark.asyncio
    async def test_link_investigation_to_source_tiger_no_existing_tags(
        self,
        workflow,
        mock_db,
        sample_investigation_id,
        sample_tiger_id
    ):
        """
        Test that _link_investigation_to_source_tiger handles tiger with no existing tags.

        Validates:
        - Creates new tags list with "investigated"
        - Handles None/empty tags gracefully
        """
        # Use a simple class to track attribute updates (Mock doesn't persist assignments)
        class MockTiger:
            def __init__(self):
                self.tiger_id = sample_tiger_id
                self.tags = None
                self.notes = ""

        source_tiger = MockTiger()
        mock_db.query.return_value.filter.return_value.first.return_value = source_tiger

        await workflow._link_investigation_to_source_tiger(
            investigation_id=sample_investigation_id,
            source_tiger_id=sample_tiger_id,
            matches={},
            report={}
        )

        # Verify tags created (tags is a list, not JSON string)
        assert "investigated" in source_tiger.tags
        assert len(source_tiger.tags) == 1

    @pytest.mark.asyncio
    async def test_link_investigation_to_source_tiger_already_investigated(
        self,
        workflow,
        mock_db,
        sample_investigation_id,
        sample_tiger_id
    ):
        """
        Test that _link_investigation_to_source_tiger doesn't duplicate "investigated" tag.

        Validates:
        - Doesn't add duplicate "investigated" tag if already present
        """
        # Mock source tiger already investigated
        # Use a simple class to track attribute updates (Mock doesn't persist assignments)
        class MockTiger:
            def __init__(self):
                self.tiger_id = sample_tiger_id
                self.tags = ["investigated", "reference"]  # List format (JSONList auto-deserializes)
                self.notes = "Previous investigation notes"

        source_tiger = MockTiger()
        mock_db.query.return_value.filter.return_value.first.return_value = source_tiger

        await workflow._link_investigation_to_source_tiger(
            investigation_id=sample_investigation_id,
            source_tiger_id=sample_tiger_id,
            matches={},
            report={}
        )

        # Verify tags not duplicated (tiger.tags is a Python list)
        assert source_tiger.tags.count("investigated") == 1

    @pytest.mark.asyncio
    async def test_link_investigation_to_source_tiger_not_found(
        self,
        workflow,
        mock_db,
        sample_investigation_id,
        sample_tiger_id
    ):
        """
        Test that _link_investigation_to_source_tiger handles missing tiger gracefully.

        Validates:
        - Returns without error when tiger not found
        - Logs warning message
        """
        # Mock tiger not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('backend.agents.investigation2_workflow.logger') as mock_logger:
            await workflow._link_investigation_to_source_tiger(
                investigation_id=sample_investigation_id,
                source_tiger_id=sample_tiger_id,
                matches={},
                report={}
            )

        # Verify warning logged
        mock_logger.warning.assert_called()
        log_msg = mock_logger.warning.call_args[0][0]
        assert "not found" in log_msg

        # Verify no commit
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_link_investigation_to_source_tiger_no_database(
        self,
        sample_investigation_id,
        sample_tiger_id
    ):
        """
        Test that _link_investigation_to_source_tiger handles missing database gracefully.

        Validates:
        - Returns without error when no database session
        """
        # Create workflow without database
        workflow = Investigation2Workflow(db=None)

        # Should not raise error
        await workflow._link_investigation_to_source_tiger(
            investigation_id=sample_investigation_id,
            source_tiger_id=sample_tiger_id,
            matches={},
            report={}
        )

        # No assertions needed - just verify no exception raised

    @pytest.mark.asyncio
    async def test_link_investigation_to_source_tiger_no_source_id(
        self,
        workflow,
        mock_db,
        sample_investigation_id
    ):
        """
        Test that _link_investigation_to_source_tiger handles missing source_tiger_id gracefully.

        Validates:
        - Returns without error when source_tiger_id is None or empty
        """
        # Call with None
        await workflow._link_investigation_to_source_tiger(
            investigation_id=sample_investigation_id,
            source_tiger_id=None,
            matches={},
            report={}
        )

        # Verify no database operations
        mock_db.query.assert_not_called()

        # Call with empty string
        await workflow._link_investigation_to_source_tiger(
            investigation_id=sample_investigation_id,
            source_tiger_id="",
            matches={},
            report={}
        )

        # Verify no database operations
        mock_db.query.assert_not_called()
