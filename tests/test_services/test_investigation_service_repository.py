"""Tests for InvestigationService repository pattern usage.

These tests verify that InvestigationService correctly delegates to InvestigationRepository
and does not bypass the repository pattern with direct session.query() calls.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from backend.services.investigation_service import InvestigationService
from backend.database.models import (
    Investigation, InvestigationStep, Evidence,
    InvestigationStatus, Priority
)
from backend.repositories.investigation_repository import InvestigationRepository


class TestInvestigationServiceRepositoryPattern:
    """Tests verifying InvestigationService uses repositories correctly."""

    def test_service_initializes_repository(self, db_session):
        """Test that service initializes repository instance."""
        service = InvestigationService(db_session)

        assert hasattr(service, 'investigation_repo')
        assert isinstance(service.investigation_repo, InvestigationRepository)
        assert service.session == db_session

    def test_create_investigation_uses_repository(self, db_session, sample_user_id):
        """Test that create_investigation delegates to repository.create()."""
        service = InvestigationService(db_session)

        # Spy on repository create method
        original_create = service.investigation_repo.create
        service.investigation_repo.create = Mock(side_effect=original_create)

        investigation = service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id,
            description="Test description",
            priority="high"
        )

        # Verify repository create was called
        service.investigation_repo.create.assert_called_once()
        assert investigation.title == "Test Investigation"
        assert investigation.priority == "high"

    def test_get_investigation_uses_repository(self, db_session, sample_user_id):
        """Test that get_investigation delegates to repository.get_by_id()."""
        service = InvestigationService(db_session)

        # Create investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Spy on repository get_by_id method
        original_get = service.investigation_repo.get_by_id
        service.investigation_repo.get_by_id = Mock(side_effect=original_get)

        # Get investigation
        retrieved = service.get_investigation(investigation.investigation_id)

        # Verify repository method was called
        service.investigation_repo.get_by_id.assert_called_once_with(investigation.investigation_id)
        assert retrieved.investigation_id == investigation.investigation_id

    def test_get_investigations_uses_repository(self, db_session, sample_user_id):
        """Test that get_investigations uses repository.get_paginated_with_filters()."""
        service = InvestigationService(db_session)

        # Create investigations
        inv1 = service.create_investigation(title="Investigation 1", created_by=sample_user_id)
        service.start_investigation(inv1.investigation_id)  # Set to active
        inv2 = service.create_investigation(title="Investigation 2", created_by=sample_user_id)

        # Spy on repository method
        original_get = service.investigation_repo.get_paginated_with_filters
        service.investigation_repo.get_paginated_with_filters = Mock(side_effect=original_get)

        # Get investigations
        investigations = service.get_investigations(limit=10, offset=0)

        # Verify repository method was called
        service.investigation_repo.get_paginated_with_filters.assert_called_once()

    def test_update_investigation_uses_repository(self, db_session, sample_user_id):
        """Test that update_investigation delegates to repository.update()."""
        service = InvestigationService(db_session)

        # Create investigation
        investigation = service.create_investigation(
            title="Original",
            created_by=sample_user_id
        )

        # Spy on repository methods
        original_get = service.investigation_repo.get_by_id
        original_update = service.investigation_repo.update
        service.investigation_repo.get_by_id = Mock(side_effect=original_get)
        service.investigation_repo.update = Mock(side_effect=original_update)

        # Update investigation
        updated = service.update_investigation(
            investigation.investigation_id,
            title="Updated"
        )

        # Verify repository methods were called
        service.investigation_repo.get_by_id.assert_called_once_with(investigation.investigation_id)
        service.investigation_repo.update.assert_called_once()
        assert updated.title == "Updated"

    def test_start_investigation_uses_repository(self, db_session, sample_user_id):
        """Test that start_investigation delegates to repository.update_status()."""
        service = InvestigationService(db_session)

        # Create investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Spy on repository method
        original_update = service.investigation_repo.update_status
        service.investigation_repo.update_status = Mock(side_effect=original_update)

        # Start investigation
        started = service.start_investigation(investigation.investigation_id)

        # Verify repository method was called
        service.investigation_repo.update_status.assert_called_once_with(
            investigation.investigation_id,
            InvestigationStatus.active
        )
        assert started.status in ["active", "in_progress"]

    def test_complete_investigation_uses_repository(self, db_session, sample_user_id):
        """Test that complete_investigation delegates to repository.update_status()."""
        service = InvestigationService(db_session)

        # Create investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Spy on repository method
        original_update = service.investigation_repo.update_status
        service.investigation_repo.update_status = Mock(side_effect=original_update)

        # Complete investigation
        completed = service.complete_investigation(investigation.investigation_id)

        # Verify repository method was called
        service.investigation_repo.update_status.assert_called_once_with(
            investigation.investigation_id,
            InvestigationStatus.completed
        )

    def test_pause_investigation_uses_repository(self, db_session, sample_user_id):
        """Test that pause_investigation uses repository methods."""
        service = InvestigationService(db_session)

        # Create and start investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )
        service.start_investigation(investigation.investigation_id)

        # Spy on repository methods
        original_get = service.investigation_repo.get_by_id
        original_update = service.investigation_repo.update
        service.investigation_repo.get_by_id = Mock(side_effect=original_get)
        service.investigation_repo.update = Mock(side_effect=original_update)

        # Pause investigation
        paused = service.pause_investigation(investigation.investigation_id)

        # Verify repository methods were called
        service.investigation_repo.get_by_id.assert_called_once()
        service.investigation_repo.update.assert_called_once()

    def test_add_investigation_step_uses_repository(self, db_session, sample_user_id):
        """Test that add_investigation_step delegates to repository.add_step()."""
        service = InvestigationService(db_session)

        # Create investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Spy on repository method
        original_add = service.investigation_repo.add_step
        service.investigation_repo.add_step = Mock(side_effect=original_add)

        # Add step
        step = service.add_investigation_step(
            investigation_id=investigation.investigation_id,
            step_type="test_step",
            agent_name="test_agent"
        )

        # Verify repository method was called
        service.investigation_repo.add_step.assert_called_once()
        assert step.step_type == "test_step"

    def test_add_evidence_uses_repository(self, db_session, sample_user_id):
        """Test that add_evidence delegates to repository.add_evidence()."""
        service = InvestigationService(db_session)

        # Create investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Spy on repository method
        original_add = service.investigation_repo.add_evidence
        service.investigation_repo.add_evidence = Mock(side_effect=original_add)

        # Add evidence
        evidence = service.add_evidence(
            investigation_id=investigation.investigation_id,
            source_type="web",
            source_url="https://example.com"
        )

        # Verify repository method was called
        service.investigation_repo.add_evidence.assert_called_once()
        assert evidence.source_type == "web"

    def test_get_investigation_steps_uses_repository(self, db_session, sample_user_id):
        """Test that get_investigation_steps delegates to repository.get_steps()."""
        service = InvestigationService(db_session)

        # Create investigation with steps
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )
        service.add_investigation_step(
            investigation_id=investigation.investigation_id,
            step_type="step1"
        )

        # Spy on repository method
        original_get = service.investigation_repo.get_steps
        service.investigation_repo.get_steps = Mock(side_effect=original_get)

        # Get steps
        steps = service.get_investigation_steps(investigation.investigation_id)

        # Verify repository method was called
        service.investigation_repo.get_steps.assert_called_once_with(investigation.investigation_id)
        assert len(steps) >= 1

    def test_get_investigation_evidence_uses_repository(self, db_session, sample_user_id):
        """Test that get_investigation_evidence delegates to repository.get_evidence()."""
        service = InvestigationService(db_session)

        # Create investigation with evidence
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )
        service.add_evidence(
            investigation_id=investigation.investigation_id,
            source_type="web"
        )

        # Spy on repository method
        original_get = service.investigation_repo.get_evidence
        service.investigation_repo.get_evidence = Mock(side_effect=original_get)

        # Get evidence
        evidence = service.get_investigation_evidence(investigation.investigation_id)

        # Verify repository method was called
        service.investigation_repo.get_evidence.assert_called_once_with(investigation.investigation_id)
        assert len(evidence) >= 1


class TestInvestigationServiceErrorHandling:
    """Tests for InvestigationService error handling with repository pattern."""

    def test_get_investigation_handles_not_found(self, db_session):
        """Test that get_investigation handles not found gracefully."""
        service = InvestigationService(db_session)

        fake_id = uuid4()
        result = service.get_investigation(fake_id)

        assert result is None

    def test_update_investigation_handles_not_found(self, db_session):
        """Test that update_investigation handles not found gracefully."""
        service = InvestigationService(db_session)

        fake_id = uuid4()
        result = service.update_investigation(fake_id, title="New Title")

        assert result is None

    def test_start_investigation_handles_not_found(self, db_session):
        """Test that start_investigation handles not found gracefully."""
        service = InvestigationService(db_session)

        fake_id = uuid4()
        result = service.start_investigation(fake_id)

        assert result is None

    def test_pause_investigation_validates_status(self, db_session, sample_user_id):
        """Test that pause_investigation validates current status."""
        service = InvestigationService(db_session)

        # Create investigation in draft status
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Try to pause draft investigation (should fail)
        with pytest.raises(ValueError, match="Cannot pause investigation"):
            service.pause_investigation(investigation.investigation_id)

    def test_resume_investigation_validates_status(self, db_session, sample_user_id):
        """Test that resume_investigation validates current status."""
        service = InvestigationService(db_session)

        # Create investigation in draft status
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Try to resume draft investigation (should fail)
        with pytest.raises(ValueError, match="Cannot resume investigation"):
            service.resume_investigation(investigation.investigation_id)

    def test_cancel_investigation_validates_status(self, db_session, sample_user_id):
        """Test that cancel_investigation validates current status."""
        service = InvestigationService(db_session)

        # Create and complete investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )
        service.complete_investigation(investigation.investigation_id)

        # Try to cancel completed investigation (should fail)
        with pytest.raises(ValueError, match="Cannot cancel investigation"):
            service.cancel_investigation(investigation.investigation_id)


class TestInvestigationServiceRepositoryIntegration:
    """Integration tests verifying repository pattern works end-to-end."""

    def test_full_investigation_lifecycle(self, db_session, sample_user_id):
        """Test complete investigation lifecycle using repository pattern."""
        service = InvestigationService(db_session)

        # Create
        investigation = service.create_investigation(
            title="Test Investigation",
            created_by=sample_user_id,
            description="Test description",
            priority="high"
        )
        assert investigation.investigation_id is not None
        assert investigation.status == "draft"

        # Start
        started = service.start_investigation(investigation.investigation_id)
        assert started.status in ["active", "in_progress"]

        # Add steps
        step1 = service.add_investigation_step(
            investigation_id=investigation.investigation_id,
            step_type="research",
            agent_name="research_agent"
        )
        step2 = service.add_investigation_step(
            investigation_id=investigation.investigation_id,
            step_type="analysis",
            agent_name="analysis_agent"
        )

        # Add evidence
        evidence1 = service.add_evidence(
            investigation_id=investigation.investigation_id,
            source_type="web",
            source_url="https://example.com"
        )

        # Retrieve steps and evidence
        steps = service.get_investigation_steps(investigation.investigation_id)
        evidence = service.get_investigation_evidence(investigation.investigation_id)
        assert len(steps) == 2
        assert len(evidence) == 1

        # Complete
        completed = service.complete_investigation(investigation.investigation_id)
        assert completed.status == "completed"

    def test_investigation_filtering_through_repository(self, db_session, sample_user_id):
        """Test that investigation filtering works through repository."""
        service = InvestigationService(db_session)

        # Create investigations with different attributes
        inv1 = service.create_investigation(
            title="High Priority",
            created_by=sample_user_id,
            priority="high"
        )
        inv2 = service.create_investigation(
            title="Low Priority",
            created_by=sample_user_id,
            priority="low"
        )
        service.start_investigation(inv1.investigation_id)

        # Filter by priority
        high_priority = service.get_investigations(priority="high")
        assert len(high_priority) >= 1
        assert all(inv.priority == "high" for inv in high_priority)

        # Filter by status
        active = service.get_investigations(status="active")
        assert len(active) >= 1

    def test_investigation_state_persistence(self, db_session, sample_user_id):
        """Test that investigation state changes persist through repository."""
        service = InvestigationService(db_session)

        # Create investigation
        investigation = service.create_investigation(
            title="Test",
            created_by=sample_user_id
        )

        # Start investigation
        service.start_investigation(investigation.investigation_id)

        # Retrieve fresh from database
        retrieved = service.get_investigation(investigation.investigation_id)
        assert retrieved.status in ["active", "in_progress"]

        # Update investigation
        service.update_investigation(
            investigation.investigation_id,
            title="Updated Title",
            description="New description"
        )

        # Verify changes persisted
        retrieved = service.get_investigation(investigation.investigation_id)
        assert retrieved.title == "Updated Title"
        assert retrieved.description == "New description"
