"""Tests for InvestigationRepository and related repositories."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import (
    Base, Investigation, InvestigationStep, Evidence,
    InvestigationStatus, Priority, User, UserRole
)
from backend.repositories.investigation_repository import (
    InvestigationRepository,
    InvestigationStepRepository,
    EvidenceRepository
)


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a database session for testing."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_user(test_session):
    """Create a sample user for testing."""
    user = User(
        username="investigator",
        email="investigator@example.com",
        password_hash="hashedpassword",
        role=UserRole.investigator.value,
        is_active=True
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def sample_investigation(test_session, sample_user):
    """Create a sample investigation for testing."""
    investigation = Investigation(
        title="Test Investigation",
        description="A test investigation",
        status=InvestigationStatus.active.value,
        priority=Priority.medium.value,
        created_by=sample_user.user_id
    )
    test_session.add(investigation)
    test_session.commit()
    test_session.refresh(investigation)
    return investigation


class TestInvestigationStepRepository:
    """Tests for InvestigationStepRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = InvestigationStepRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == InvestigationStep

    def test_get_by_investigation_id(self, test_session, sample_investigation):
        """Test getting steps for an investigation."""
        repo = InvestigationStepRepository(test_session)

        # Create steps with different timestamps
        now = datetime.utcnow()
        for i in range(3):
            step = InvestigationStep(
                investigation_id=sample_investigation.investigation_id,
                step_type=f"step_{i}",
                description=f"Step {i} description",
                timestamp=now + timedelta(minutes=i)
            )
            repo.create(step)

        steps = repo.get_by_investigation_id(sample_investigation.investigation_id)

        assert len(steps) == 3
        # Should be ordered by timestamp
        assert steps[0].step_type == "step_0"
        assert steps[2].step_type == "step_2"

    def test_get_by_investigation_id_no_order(self, test_session, sample_investigation):
        """Test getting steps without timestamp ordering."""
        repo = InvestigationStepRepository(test_session)

        for i in range(3):
            step = InvestigationStep(
                investigation_id=sample_investigation.investigation_id,
                step_type=f"step_{i}",
                description=f"Step {i}"
            )
            repo.create(step)

        steps = repo.get_by_investigation_id(
            sample_investigation.investigation_id,
            order_by_timestamp=False
        )

        assert len(steps) == 3

    def test_get_by_step_type(self, test_session, sample_investigation):
        """Test getting a specific step type."""
        repo = InvestigationStepRepository(test_session)

        # Create steps of different types
        step_types = ["upload", "detection", "analysis", "report"]
        for step_type in step_types:
            step = InvestigationStep(
                investigation_id=sample_investigation.investigation_id,
                step_type=step_type,
                description=f"{step_type} step"
            )
            repo.create(step)

        found = repo.get_by_step_type(
            sample_investigation.investigation_id,
            "detection"
        )

        assert found is not None
        assert found.step_type == "detection"

    def test_get_by_step_type_not_found(self, test_session, sample_investigation):
        """Test getting non-existent step type."""
        repo = InvestigationStepRepository(test_session)

        found = repo.get_by_step_type(
            sample_investigation.investigation_id,
            "nonexistent"
        )

        assert found is None

    def test_get_latest_step(self, test_session, sample_investigation):
        """Test getting the latest step."""
        repo = InvestigationStepRepository(test_session)

        now = datetime.utcnow()
        for i in range(4):
            step = InvestigationStep(
                investigation_id=sample_investigation.investigation_id,
                step_type=f"step_{i}",
                description=f"Step {i}",
                timestamp=now + timedelta(minutes=i)
            )
            repo.create(step)

        latest = repo.get_latest_step(sample_investigation.investigation_id)

        assert latest is not None
        assert latest.step_type == "step_3"


class TestEvidenceRepository:
    """Tests for EvidenceRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = EvidenceRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == Evidence

    def test_get_by_investigation_id(self, test_session, sample_investigation):
        """Test getting evidence for an investigation."""
        repo = EvidenceRepository(test_session)

        # Create evidence items
        for i in range(4):
            evidence = Evidence(
                investigation_id=sample_investigation.investigation_id,
                title=f"Evidence {i}",
                description=f"Description {i}",
                verified=(i % 2 == 0)
            )
            repo.create(evidence)

        all_evidence = repo.get_by_investigation_id(sample_investigation.investigation_id)

        assert len(all_evidence) == 4

    def test_get_verified_evidence(self, test_session, sample_investigation):
        """Test getting only verified evidence."""
        repo = EvidenceRepository(test_session)

        # Create mixed verified/unverified evidence
        for i in range(5):
            evidence = Evidence(
                investigation_id=sample_investigation.investigation_id,
                title=f"Evidence {i}",
                description=f"Description {i}",
                verified=(i < 3)  # First 3 are verified
            )
            repo.create(evidence)

        verified = repo.get_verified_evidence(sample_investigation.investigation_id)

        assert len(verified) == 3
        assert all(e.verified for e in verified)


class TestInvestigationRepository:
    """Tests for InvestigationRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = InvestigationRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == Investigation
        assert repo.step_repo is not None
        assert repo.evidence_repo is not None

    def test_get_by_id(self, test_session, sample_investigation):
        """Test getting investigation by ID."""
        repo = InvestigationRepository(test_session)

        found = repo.get_by_id(sample_investigation.investigation_id)

        assert found is not None
        assert found.investigation_id == sample_investigation.investigation_id
        assert found.title == "Test Investigation"

    def test_get_by_id_not_found(self, test_session):
        """Test getting investigation by non-existent ID."""
        repo = InvestigationRepository(test_session)

        found = repo.get_by_id(uuid4())

        assert found is None

    def test_get_by_creator(self, test_session, sample_user):
        """Test getting investigations by creator."""
        repo = InvestigationRepository(test_session)

        # Create investigations for the user
        for i in range(3):
            investigation = Investigation(
                title=f"User Investigation {i}",
                description=f"Description {i}",
                status=InvestigationStatus.active.value,
                priority=Priority.medium.value,
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        # Create investigation for different user
        other_user = User(
            username="other",
            email="other@example.com",
            password_hash="hashedpassword",
            role=UserRole.investigator.value,
            is_active=True
        )
        test_session.add(other_user)
        test_session.commit()

        investigation = Investigation(
            title="Other Investigation",
            description="Other description",
            status=InvestigationStatus.active.value,
            priority=Priority.medium.value,
            created_by=other_user.user_id
        )
        repo.create(investigation)

        user_investigations = repo.get_by_creator(sample_user.user_id)

        assert len(user_investigations) == 3
        assert all(inv.created_by == sample_user.user_id for inv in user_investigations)

    def test_get_by_status(self, test_session, sample_user):
        """Test getting investigations by status."""
        repo = InvestigationRepository(test_session)

        # Create investigations with different statuses
        statuses = [
            InvestigationStatus.active,
            InvestigationStatus.completed,
            InvestigationStatus.active,
            InvestigationStatus.draft
        ]
        for i, status in enumerate(statuses):
            investigation = Investigation(
                title=f"Status Investigation {i}",
                description=f"Description {i}",
                status=status.value,
                priority=Priority.medium.value,
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        active = repo.get_by_status(InvestigationStatus.active)

        assert len(active) == 2

    def test_get_active_investigations(self, test_session, sample_user):
        """Test getting active investigations."""
        repo = InvestigationRepository(test_session)

        # Create investigations with different statuses
        active_statuses = [
            InvestigationStatus.draft,
            InvestigationStatus.active,
            InvestigationStatus.pending_verification
        ]
        inactive_statuses = [
            InvestigationStatus.completed,
            InvestigationStatus.archived
        ]

        for i, status in enumerate(active_statuses):
            investigation = Investigation(
                title=f"Active Investigation {i}",
                description=f"Description {i}",
                status=status.value,
                priority=Priority.medium.value,
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        for i, status in enumerate(inactive_statuses):
            investigation = Investigation(
                title=f"Inactive Investigation {i}",
                description=f"Description {i}",
                status=status.value,
                priority=Priority.medium.value,
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        active = repo.get_active_investigations()

        assert len(active) == 3

    def test_get_by_priority(self, test_session, sample_user):
        """Test getting investigations by priority."""
        repo = InvestigationRepository(test_session)

        priorities = [Priority.low, Priority.high, Priority.medium, Priority.high, Priority.critical]
        for i, priority in enumerate(priorities):
            investigation = Investigation(
                title=f"Priority Investigation {i}",
                description=f"Description {i}",
                status=InvestigationStatus.active.value,
                priority=priority.value,
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        high_priority = repo.get_by_priority(Priority.high)

        assert len(high_priority) == 2

    def test_get_high_priority(self, test_session, sample_user):
        """Test getting high and critical priority investigations."""
        repo = InvestigationRepository(test_session)

        priorities = [Priority.low, Priority.high, Priority.medium, Priority.high, Priority.critical]
        for i, priority in enumerate(priorities):
            investigation = Investigation(
                title=f"Priority Investigation {i}",
                description=f"Description {i}",
                status=InvestigationStatus.active.value,
                priority=priority.value,
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        high_priority = repo.get_high_priority()

        assert len(high_priority) == 3  # 2 high + 1 critical

    def test_search_investigations(self, test_session, sample_user):
        """Test searching investigations."""
        repo = InvestigationRepository(test_session)

        # Create investigations with different titles/descriptions
        data = [
            ("Tiger Trafficking Case", "Investigation into tiger trafficking"),
            ("Wildlife Trade Analysis", "Analyzing wildlife trade patterns"),
            ("Tiger Cubs Seizure", "Investigation of tiger cub seizure"),
            ("Import Violation", "Import documentation violations")
        ]
        for title, desc in data:
            investigation = Investigation(
                title=title,
                description=desc,
                status=InvestigationStatus.active.value,
                priority=Priority.medium.value,
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        # Search by title
        result = repo.search("Tiger", page=1, page_size=10)
        assert result.total == 2

        # Search by description
        result = repo.search("wildlife", page=1, page_size=10)
        assert result.total == 1

    def test_get_paginated_with_filters(self, test_session, sample_user):
        """Test paginated results with filters."""
        repo = InvestigationRepository(test_session)

        # Create investigations with various attributes
        for i in range(6):
            investigation = Investigation(
                title=f"Filter Investigation {i}",
                description=f"Description {i}",
                status=(InvestigationStatus.active.value if i < 4
                        else InvestigationStatus.completed.value),
                priority=(Priority.high.value if i < 2 else Priority.medium.value),
                created_by=sample_user.user_id
            )
            repo.create(investigation)

        # Filter by status
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            status=InvestigationStatus.active
        )
        assert result.total == 4

        # Filter by priority
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            priority=Priority.high
        )
        assert result.total == 2

        # Filter by creator
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            created_by=sample_user.user_id
        )
        assert result.total == 6

    def test_update_status(self, test_session, sample_investigation):
        """Test updating investigation status."""
        repo = InvestigationRepository(test_session)

        assert sample_investigation.status == InvestigationStatus.active.value
        assert sample_investigation.completed_at is None

        updated = repo.update_status(
            sample_investigation.investigation_id,
            InvestigationStatus.completed
        )

        assert updated is not None
        assert updated.status == InvestigationStatus.completed.value
        assert updated.completed_at is not None

    def test_update_status_sets_started_at(self, test_session, sample_user):
        """Test that updating to active sets started_at."""
        repo = InvestigationRepository(test_session)

        investigation = Investigation(
            title="Draft Investigation",
            description="A draft",
            status=InvestigationStatus.draft.value,
            priority=Priority.medium.value,
            created_by=sample_user.user_id
        )
        created = repo.create(investigation)

        assert created.started_at is None

        updated = repo.update_status(
            created.investigation_id,
            InvestigationStatus.active
        )

        assert updated.started_at is not None

    def test_update_status_not_found(self, test_session):
        """Test updating status for non-existent investigation."""
        repo = InvestigationRepository(test_session)

        result = repo.update_status(uuid4(), InvestigationStatus.completed)

        assert result is None

    def test_add_tiger(self, test_session, sample_investigation):
        """Test adding a tiger to investigation."""
        repo = InvestigationRepository(test_session)

        tiger_id = uuid4()

        updated = repo.add_tiger(sample_investigation.investigation_id, tiger_id)

        assert updated is not None
        assert str(tiger_id) in updated.related_tigers

    def test_add_tiger_duplicate(self, test_session, sample_investigation):
        """Test adding same tiger twice doesn't duplicate."""
        repo = InvestigationRepository(test_session)

        tiger_id = uuid4()

        # Add first time
        repo.add_tiger(sample_investigation.investigation_id, tiger_id)

        # Add second time
        updated = repo.add_tiger(sample_investigation.investigation_id, tiger_id)

        # Should only appear once
        assert updated.related_tigers.count(str(tiger_id)) == 1

    def test_add_facility(self, test_session, sample_investigation):
        """Test adding a facility to investigation."""
        repo = InvestigationRepository(test_session)

        facility_id = uuid4()

        updated = repo.add_facility(sample_investigation.investigation_id, facility_id)

        assert updated is not None
        assert str(facility_id) in updated.related_facilities

    def test_get_steps(self, test_session, sample_investigation):
        """Test getting steps via main repository."""
        repo = InvestigationRepository(test_session)

        # Create steps
        for i in range(3):
            step = InvestigationStep(
                investigation_id=sample_investigation.investigation_id,
                step_type=f"step_{i}",
                description=f"Step {i}"
            )
            test_session.add(step)
        test_session.commit()

        steps = repo.get_steps(sample_investigation.investigation_id)

        assert len(steps) == 3

    def test_add_step(self, test_session, sample_investigation):
        """Test adding a step via main repository."""
        repo = InvestigationRepository(test_session)

        step = InvestigationStep(
            investigation_id=sample_investigation.investigation_id,
            step_type="detection",
            description="Running tiger detection"
        )

        created = repo.add_step(step)

        assert created.step_id is not None
        assert created.step_type == "detection"

    def test_get_evidence(self, test_session, sample_investigation):
        """Test getting evidence via main repository."""
        repo = InvestigationRepository(test_session)

        # Create evidence
        for i in range(2):
            evidence = Evidence(
                investigation_id=sample_investigation.investigation_id,
                title=f"Evidence {i}",
                description=f"Description {i}"
            )
            test_session.add(evidence)
        test_session.commit()

        evidence = repo.get_evidence(sample_investigation.investigation_id)

        assert len(evidence) == 2

    def test_add_evidence(self, test_session, sample_investigation):
        """Test adding evidence via main repository."""
        repo = InvestigationRepository(test_session)

        evidence = Evidence(
            investigation_id=sample_investigation.investigation_id,
            title="New Evidence",
            description="Description of evidence"
        )

        created = repo.add_evidence(evidence)

        assert created.evidence_id is not None
        assert created.title == "New Evidence"
