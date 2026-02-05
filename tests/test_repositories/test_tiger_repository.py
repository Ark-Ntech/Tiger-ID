"""Tests for TigerRepository and TigerImageRepository classes."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base, Tiger, TigerImage, TigerStatus, Facility
from backend.repositories.tiger_repository import TigerRepository, TigerImageRepository


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
def sample_tiger(test_session):
    """Create a sample tiger for testing."""
    tiger = Tiger(
        name="Test Tiger",
        alias="TT001",
        status=TigerStatus.active.value,
        is_reference=False
    )
    test_session.add(tiger)
    test_session.commit()
    test_session.refresh(tiger)
    return tiger


@pytest.fixture
def sample_facility(test_session):
    """Create a sample facility for testing."""
    facility = Facility(
        exhibitor_name="Test Facility",
        usda_license="12-ABC-0001",
        state="TX",
        city="Houston"
    )
    test_session.add(facility)
    test_session.commit()
    test_session.refresh(facility)
    return facility


class TestTigerImageRepository:
    """Tests for TigerImageRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = TigerImageRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == TigerImage

    def test_get_by_tiger_id(self, test_session, sample_tiger):
        """Test getting images for a tiger."""
        repo = TigerImageRepository(test_session)

        # Create images for the tiger
        for i in range(3):
            image = TigerImage(
                tiger_id=sample_tiger.tiger_id,
                image_path=f"/path/to/image{i}.jpg",
                verified=True
            )
            repo.create(image)

        images = repo.get_by_tiger_id(sample_tiger.tiger_id)

        assert len(images) == 3
        assert all(img.tiger_id == sample_tiger.tiger_id for img in images)

    def test_get_by_tiger_id_empty(self, test_session):
        """Test getting images for a tiger with no images."""
        repo = TigerImageRepository(test_session)

        images = repo.get_by_tiger_id(uuid4())

        assert len(images) == 0

    def test_get_verified_images(self, test_session, sample_tiger):
        """Test getting only verified images."""
        repo = TigerImageRepository(test_session)

        # Create mixed verified/unverified images
        for i in range(4):
            image = TigerImage(
                tiger_id=sample_tiger.tiger_id,
                image_path=f"/path/to/image{i}.jpg",
                verified=(i % 2 == 0)  # Alternating verified status
            )
            repo.create(image)

        verified_images = repo.get_verified_images(sample_tiger.tiger_id)

        assert len(verified_images) == 2
        assert all(img.verified for img in verified_images)

    def test_get_reference_images(self, test_session):
        """Test getting reference images."""
        repo = TigerImageRepository(test_session)

        # Create a reference tiger
        ref_tiger = Tiger(
            name="Reference Tiger",
            is_reference=True,
            status=TigerStatus.active.value
        )
        test_session.add(ref_tiger)
        test_session.commit()

        # Create reference and non-reference images
        for i in range(3):
            image = TigerImage(
                tiger_id=ref_tiger.tiger_id,
                image_path=f"/path/to/ref{i}.jpg",
                is_reference=True,
                verified=True
            )
            repo.create(image)

        # Create non-reference image
        non_ref_tiger = Tiger(
            name="Non-Ref Tiger",
            is_reference=False,
            status=TigerStatus.active.value
        )
        test_session.add(non_ref_tiger)
        test_session.commit()

        non_ref_image = TigerImage(
            tiger_id=non_ref_tiger.tiger_id,
            image_path="/path/to/nonref.jpg",
            is_reference=False,
            verified=True
        )
        repo.create(non_ref_image)

        ref_images = repo.get_reference_images()

        assert len(ref_images) == 3
        assert all(img.is_reference for img in ref_images)


class TestTigerRepository:
    """Tests for TigerRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = TigerRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == Tiger
        assert repo.image_repo is not None

    def test_get_by_id(self, test_session, sample_tiger):
        """Test getting tiger by ID."""
        repo = TigerRepository(test_session)

        found = repo.get_by_id(sample_tiger.tiger_id)

        assert found is not None
        assert found.tiger_id == sample_tiger.tiger_id
        assert found.name == "Test Tiger"

    def test_get_by_id_not_found(self, test_session):
        """Test getting tiger by non-existent ID."""
        repo = TigerRepository(test_session)

        found = repo.get_by_id(uuid4())

        assert found is None

    def test_get_by_name(self, test_session, sample_tiger):
        """Test getting tiger by name."""
        repo = TigerRepository(test_session)

        found = repo.get_by_name("Test Tiger")

        assert found is not None
        assert found.name == "Test Tiger"

    def test_get_by_name_not_found(self, test_session):
        """Test getting tiger by non-existent name."""
        repo = TigerRepository(test_session)

        found = repo.get_by_name("Does Not Exist")

        assert found is None

    def test_get_by_alias(self, test_session, sample_tiger):
        """Test getting tiger by alias."""
        repo = TigerRepository(test_session)

        found = repo.get_by_alias("TT001")

        assert found is not None
        assert found.alias == "TT001"

    def test_get_by_facility(self, test_session, sample_facility):
        """Test getting tigers at a facility."""
        repo = TigerRepository(test_session)

        # Create tigers at the facility
        for i in range(3):
            tiger = Tiger(
                name=f"Facility Tiger {i}",
                origin_facility_id=sample_facility.facility_id,
                status=TigerStatus.active.value
            )
            repo.create(tiger)

        tigers = repo.get_by_facility(sample_facility.facility_id)

        assert len(tigers) == 3
        assert all(t.origin_facility_id == sample_facility.facility_id for t in tigers)

    def test_get_by_status(self, test_session):
        """Test getting tigers by status."""
        repo = TigerRepository(test_session)

        # Create tigers with different statuses
        statuses = [TigerStatus.active, TigerStatus.monitored, TigerStatus.active, TigerStatus.seized]
        for i, status in enumerate(statuses):
            tiger = Tiger(
                name=f"Status Tiger {i}",
                status=status.value
            )
            repo.create(tiger)

        active_tigers = repo.get_by_status(TigerStatus.active)

        assert len(active_tigers) == 2

    def test_get_reference_tigers(self, test_session):
        """Test getting reference tigers."""
        repo = TigerRepository(test_session)

        # Create reference and non-reference tigers
        for i in range(3):
            tiger = Tiger(
                name=f"Reference Tiger {i}",
                is_reference=True,
                status=TigerStatus.active.value
            )
            repo.create(tiger)

        for i in range(2):
            tiger = Tiger(
                name=f"Discovered Tiger {i}",
                is_reference=False,
                status=TigerStatus.active.value
            )
            repo.create(tiger)

        ref_tigers = repo.get_reference_tigers()

        assert len(ref_tigers) == 3
        assert all(t.is_reference for t in ref_tigers)

    def test_get_discovered_tigers(self, test_session):
        """Test getting discovered (non-reference) tigers."""
        repo = TigerRepository(test_session)

        # Create reference and non-reference tigers
        for i in range(2):
            tiger = Tiger(
                name=f"Reference Tiger {i}",
                is_reference=True,
                status=TigerStatus.active.value
            )
            repo.create(tiger)

        for i in range(4):
            tiger = Tiger(
                name=f"Discovered Tiger {i}",
                is_reference=False,
                status=TigerStatus.active.value
            )
            repo.create(tiger)

        discovered = repo.get_discovered_tigers()

        assert len(discovered) == 4
        assert all(not t.is_reference for t in discovered)

    def test_get_recently_seen(self, test_session):
        """Test getting recently seen tigers."""
        repo = TigerRepository(test_session)

        # Create tigers with different last_seen_date
        now = datetime.utcnow()
        for i in range(5):
            tiger = Tiger(
                name=f"Seen Tiger {i}",
                status=TigerStatus.active.value,
                last_seen_date=now - timedelta(days=i)
            )
            repo.create(tiger)

        # Create tiger without last_seen_date
        tiger = Tiger(
            name="Never Seen Tiger",
            status=TigerStatus.active.value
        )
        repo.create(tiger)

        recent = repo.get_recently_seen(limit=3)

        assert len(recent) == 3
        # Should be ordered by most recent first
        assert recent[0].name == "Seen Tiger 0"
        assert recent[1].name == "Seen Tiger 1"
        assert recent[2].name == "Seen Tiger 2"

    def test_get_with_images(self, test_session, sample_tiger):
        """Test getting tiger with associated images."""
        repo = TigerRepository(test_session)

        # Create images for the tiger
        for i in range(3):
            image = TigerImage(
                tiger_id=sample_tiger.tiger_id,
                image_path=f"/path/to/image{i}.jpg",
                verified=True
            )
            test_session.add(image)
        test_session.commit()

        result = repo.get_with_images(sample_tiger.tiger_id)

        assert result is not None
        assert result["tiger"].tiger_id == sample_tiger.tiger_id
        assert result["image_count"] == 3
        assert len(result["images"]) == 3

    def test_get_with_images_not_found(self, test_session):
        """Test getting tiger with images when tiger doesn't exist."""
        repo = TigerRepository(test_session)

        result = repo.get_with_images(uuid4())

        assert result is None

    def test_get_related_tigers(self, test_session, sample_facility):
        """Test getting related tigers (same facility)."""
        repo = TigerRepository(test_session)

        # Create tigers at the same facility
        tigers = []
        for i in range(4):
            tiger = Tiger(
                name=f"Related Tiger {i}",
                origin_facility_id=sample_facility.facility_id,
                status=TigerStatus.active.value
            )
            repo.create(tiger)
            tigers.append(tiger)

        # Get related tigers for first tiger
        related = repo.get_related_tigers(tigers[0].tiger_id, limit=5)

        # Should return other tigers at same facility, excluding the query tiger
        assert len(related) == 3
        assert all(t.tiger_id != tigers[0].tiger_id for t in related)
        assert all(t.origin_facility_id == sample_facility.facility_id for t in related)

    def test_get_related_tigers_no_facility(self, test_session, sample_tiger):
        """Test getting related tigers when tiger has no facility."""
        repo = TigerRepository(test_session)

        # sample_tiger has no origin_facility_id
        related = repo.get_related_tigers(sample_tiger.tiger_id)

        assert len(related) == 0

    def test_search_tigers(self, test_session):
        """Test searching tigers by name."""
        repo = TigerRepository(test_session)

        # Create tigers with different names
        names = ["Alpha Tiger", "Beta Lion", "Alpha Cat", "Gamma Tiger"]
        for name in names:
            tiger = Tiger(
                name=name,
                status=TigerStatus.active.value
            )
            repo.create(tiger)

        # Search for "Alpha"
        result = repo.search("Alpha", page=1, page_size=10)

        assert result.total == 2
        assert all("Alpha" in t.name for t in result.items)

    def test_get_paginated_with_filters(self, test_session, sample_facility):
        """Test paginated results with filters."""
        repo = TigerRepository(test_session)

        # Create tigers with different attributes
        for i in range(5):
            tiger = Tiger(
                name=f"Active Tiger {i}",
                status=TigerStatus.active.value,
                is_reference=False,
                origin_facility_id=sample_facility.facility_id
            )
            repo.create(tiger)

        for i in range(3):
            tiger = Tiger(
                name=f"Reference Tiger {i}",
                status=TigerStatus.active.value,
                is_reference=True
            )
            repo.create(tiger)

        # Filter by facility
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            facility_id=sample_facility.facility_id
        )
        assert result.total == 5

        # Filter by reference status
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            is_reference=True
        )
        assert result.total == 3

        # Filter by status
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            status=TigerStatus.active
        )
        assert result.total == 8

    def test_update_last_seen(self, test_session, sample_tiger):
        """Test updating tiger's last seen information."""
        repo = TigerRepository(test_session)

        seen_date = datetime.utcnow()
        location = "Houston, TX"

        updated = repo.update_last_seen(
            sample_tiger.tiger_id,
            location=location,
            seen_date=seen_date
        )

        assert updated is not None
        assert updated.last_seen_location == location
        assert updated.last_seen_date == seen_date

    def test_update_last_seen_not_found(self, test_session):
        """Test updating last seen for non-existent tiger."""
        repo = TigerRepository(test_session)

        result = repo.update_last_seen(
            uuid4(),
            location="Somewhere",
            seen_date=datetime.utcnow()
        )

        assert result is None

    def test_get_images(self, test_session, sample_tiger):
        """Test getting images for a tiger via repository."""
        repo = TigerRepository(test_session)

        # Create images
        for i in range(2):
            image = TigerImage(
                tiger_id=sample_tiger.tiger_id,
                image_path=f"/path/to/image{i}.jpg",
                verified=True
            )
            test_session.add(image)
        test_session.commit()

        images = repo.get_images(sample_tiger.tiger_id)

        assert len(images) == 2

    def test_add_image(self, test_session, sample_tiger):
        """Test adding an image to a tiger."""
        repo = TigerRepository(test_session)

        image = TigerImage(
            tiger_id=sample_tiger.tiger_id,
            image_path="/path/to/new_image.jpg",
            verified=False
        )

        created = repo.add_image(image)

        assert created.image_id is not None
        assert created.tiger_id == sample_tiger.tiger_id
        assert created.image_path == "/path/to/new_image.jpg"
