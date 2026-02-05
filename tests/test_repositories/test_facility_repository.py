"""Tests for FacilityRepository class."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base, Facility, Investigation, InvestigationStatus
from backend.repositories.facility_repository import FacilityRepository


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
def sample_facility(test_session):
    """Create a sample facility for testing."""
    facility = Facility(
        exhibitor_name="Test Zoo",
        usda_license="12-ABC-0001",
        state="TX",
        city="Houston",
        address="123 Zoo Lane",
        tiger_count=5
    )
    test_session.add(facility)
    test_session.commit()
    test_session.refresh(facility)
    return facility


class TestFacilityRepository:
    """Tests for FacilityRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = FacilityRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == Facility

    def test_get_by_id(self, test_session, sample_facility):
        """Test getting facility by ID."""
        repo = FacilityRepository(test_session)

        found = repo.get_by_id(sample_facility.facility_id)

        assert found is not None
        assert found.facility_id == sample_facility.facility_id
        assert found.exhibitor_name == "Test Zoo"

    def test_get_by_id_not_found(self, test_session):
        """Test getting facility by non-existent ID."""
        repo = FacilityRepository(test_session)

        found = repo.get_by_id(uuid4())

        assert found is None

    def test_get_by_usda_license(self, test_session, sample_facility):
        """Test getting facility by USDA license."""
        repo = FacilityRepository(test_session)

        found = repo.get_by_usda_license("12-ABC-0001")

        assert found is not None
        assert found.usda_license == "12-ABC-0001"

    def test_get_by_usda_license_not_found(self, test_session):
        """Test getting facility by non-existent USDA license."""
        repo = FacilityRepository(test_session)

        found = repo.get_by_usda_license("99-XXX-9999")

        assert found is None

    def test_get_by_exhibitor_name(self, test_session, sample_facility):
        """Test getting facility by exhibitor name."""
        repo = FacilityRepository(test_session)

        found = repo.get_by_exhibitor_name("Test Zoo")

        assert found is not None
        assert found.exhibitor_name == "Test Zoo"

    def test_get_by_state(self, test_session):
        """Test getting facilities by state."""
        repo = FacilityRepository(test_session)

        # Create facilities in different states
        states = ["TX", "FL", "TX", "CA", "TX"]
        for i, state in enumerate(states):
            facility = Facility(
                exhibitor_name=f"Facility {i}",
                usda_license=f"00-XXX-{i:04d}",
                state=state,
                city=f"City {i}"
            )
            repo.create(facility)

        texas_facilities = repo.get_by_state("TX")

        assert len(texas_facilities) == 3
        assert all(f.state == "TX" for f in texas_facilities)

    def test_get_by_city(self, test_session):
        """Test getting facilities by city."""
        repo = FacilityRepository(test_session)

        # Create facilities in different cities
        for i in range(3):
            facility = Facility(
                exhibitor_name=f"Houston Facility {i}",
                usda_license=f"00-HOU-{i:04d}",
                state="TX",
                city="Houston"
            )
            repo.create(facility)

        facility = Facility(
            exhibitor_name="Dallas Facility",
            usda_license="00-DAL-0001",
            state="TX",
            city="Dallas"
        )
        repo.create(facility)

        houston_facilities = repo.get_by_city("Houston")

        assert len(houston_facilities) == 3

    def test_get_by_city_with_state(self, test_session):
        """Test getting facilities by city with state filter."""
        repo = FacilityRepository(test_session)

        # Create facilities in same city but different states
        facility = Facility(
            exhibitor_name="Springfield TX",
            usda_license="00-SPR-0001",
            state="TX",
            city="Springfield"
        )
        repo.create(facility)

        facility = Facility(
            exhibitor_name="Springfield IL",
            usda_license="00-SPR-0002",
            state="IL",
            city="Springfield"
        )
        repo.create(facility)

        # Without state filter
        all_springfield = repo.get_by_city("Springfield")
        assert len(all_springfield) == 2

        # With state filter
        tx_springfield = repo.get_by_city("Springfield", state="TX")
        assert len(tx_springfield) == 1
        assert tx_springfield[0].state == "TX"

    def test_get_reference_facilities(self, test_session):
        """Test getting reference facilities."""
        repo = FacilityRepository(test_session)

        # Create reference facilities
        for i in range(3):
            facility = Facility(
                exhibitor_name=f"Reference Facility {i}",
                usda_license=f"00-REF-{i:04d}",
                state="TX",
                city="Reference City",
                is_reference_facility=True
            )
            repo.create(facility)

        # Create non-reference facility
        facility = Facility(
            exhibitor_name="Non-Reference Facility",
            usda_license="00-NON-0001",
            state="TX",
            city="Non-Ref City",
            is_reference_facility=False
        )
        repo.create(facility)

        ref_facilities = repo.get_reference_facilities()

        assert len(ref_facilities) == 3
        assert all(f.is_reference_facility for f in ref_facilities)

    def test_get_discovered_facilities(self, test_session):
        """Test getting discovered facilities."""
        repo = FacilityRepository(test_session)

        now = datetime.utcnow()

        # Create discovered facilities
        for i in range(2):
            facility = Facility(
                exhibitor_name=f"Discovered Facility {i}",
                usda_license=f"00-DIS-{i:04d}",
                state="FL",
                city="Discovery City",
                discovered_at=now - timedelta(days=i)
            )
            repo.create(facility)

        # Create non-discovered facility
        facility = Facility(
            exhibitor_name="Not Discovered",
            usda_license="00-NOT-0001",
            state="FL",
            city="Not Discovered City"
        )
        repo.create(facility)

        discovered = repo.get_discovered_facilities()

        assert len(discovered) == 2
        assert all(f.discovered_at is not None for f in discovered)

    def test_get_with_tigers(self, test_session):
        """Test getting facilities with tigers."""
        repo = FacilityRepository(test_session)

        # Create facilities with different tiger counts
        for i, count in enumerate([0, 3, 5, 0, 10]):
            facility = Facility(
                exhibitor_name=f"Tiger Facility {i}",
                usda_license=f"00-TIG-{i:04d}",
                state="TX",
                city="Tiger City",
                tiger_count=count
            )
            repo.create(facility)

        # Get facilities with at least 1 tiger
        with_tigers = repo.get_with_tigers(min_tiger_count=1)

        assert len(with_tigers) == 3
        # Should be sorted by tiger count descending
        assert with_tigers[0].tiger_count == 10
        assert with_tigers[1].tiger_count == 5
        assert with_tigers[2].tiger_count == 3

    def test_get_recently_crawled(self, test_session):
        """Test getting recently crawled facilities."""
        repo = FacilityRepository(test_session)

        now = datetime.utcnow()

        # Create crawled facilities
        for i in range(5):
            facility = Facility(
                exhibitor_name=f"Crawled Facility {i}",
                usda_license=f"00-CRL-{i:04d}",
                state="TX",
                city="Crawl City",
                last_crawled_at=now - timedelta(hours=i)
            )
            repo.create(facility)

        # Create never crawled facility
        facility = Facility(
            exhibitor_name="Never Crawled",
            usda_license="00-NVR-0001",
            state="TX",
            city="Never Crawled City"
        )
        repo.create(facility)

        recent = repo.get_recently_crawled(limit=3)

        assert len(recent) == 3
        assert recent[0].exhibitor_name == "Crawled Facility 0"  # Most recent

    def test_get_needing_crawl(self, test_session):
        """Test getting facilities needing crawl."""
        repo = FacilityRepository(test_session)

        now = datetime.utcnow()

        # Create recently crawled facilities
        for i in range(2):
            facility = Facility(
                exhibitor_name=f"Recently Crawled {i}",
                usda_license=f"00-REC-{i:04d}",
                state="TX",
                city="Recent City",
                last_crawled_at=now - timedelta(days=1)
            )
            repo.create(facility)

        # Create stale facilities (crawled long ago)
        for i in range(3):
            facility = Facility(
                exhibitor_name=f"Stale Facility {i}",
                usda_license=f"00-STL-{i:04d}",
                state="TX",
                city="Stale City",
                last_crawled_at=now - timedelta(days=10)
            )
            repo.create(facility)

        # Create never crawled facilities
        for i in range(2):
            facility = Facility(
                exhibitor_name=f"Never Crawled {i}",
                usda_license=f"00-NVR-{i:04d}",
                state="TX",
                city="Never City"
            )
            repo.create(facility)

        # Get facilities needing crawl (not crawled in 7 days)
        needing_crawl = repo.get_needing_crawl(days_since_crawl=7, limit=10)

        # Should return never crawled (2) + stale (3)
        assert len(needing_crawl) == 5

        # Never crawled should come first (null values first)
        assert needing_crawl[0].last_crawled_at is None or needing_crawl[1].last_crawled_at is None

    def test_search_facilities(self, test_session):
        """Test searching facilities."""
        repo = FacilityRepository(test_session)

        # Create facilities with searchable attributes
        names = ["Big Cat Rescue", "Tiger Paradise", "Wildlife Sanctuary", "Big Cat Haven"]
        for i, name in enumerate(names):
            facility = Facility(
                exhibitor_name=name,
                usda_license=f"00-SRC-{i:04d}",
                state="FL" if i < 2 else "TX",
                city="Miami" if i < 2 else "Austin",
                address=f"{i}00 Main St"
            )
            repo.create(facility)

        # Search by name
        result = repo.search("Big Cat", page=1, page_size=10)
        assert result.total == 2

        # Search by state
        result = repo.search("TX", page=1, page_size=10)
        assert result.total == 2

        # Search by city
        result = repo.search("Miami", page=1, page_size=10)
        assert result.total == 2

    def test_get_paginated_with_filters(self, test_session):
        """Test paginated results with filters."""
        repo = FacilityRepository(test_session)

        # Create facilities with different attributes
        for i in range(5):
            facility = Facility(
                exhibitor_name=f"Filter Test Facility {i}",
                usda_license=f"00-FLT-{i:04d}",
                state="TX" if i < 3 else "FL",
                city=f"City {i}",
                tiger_count=i * 2,
                is_reference_facility=(i < 2)
            )
            repo.create(facility)

        # Filter by state
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            state="TX"
        )
        assert result.total == 3

        # Filter by reference status
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            is_reference=True
        )
        assert result.total == 2

        # Filter by has_tigers
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            has_tigers=True
        )
        assert result.total == 4  # All except the one with 0 tigers

    def test_update_tiger_count(self, test_session, sample_facility):
        """Test updating facility's tiger count."""
        repo = FacilityRepository(test_session)

        assert sample_facility.tiger_count == 5

        updated = repo.update_tiger_count(sample_facility.facility_id, 10)

        assert updated is not None
        assert updated.tiger_count == 10

    def test_update_tiger_count_not_found(self, test_session):
        """Test updating tiger count for non-existent facility."""
        repo = FacilityRepository(test_session)

        result = repo.update_tiger_count(uuid4(), 10)

        assert result is None

    def test_update_crawl_timestamp(self, test_session, sample_facility):
        """Test updating facility's last crawled timestamp."""
        repo = FacilityRepository(test_session)

        assert sample_facility.last_crawled_at is None

        updated = repo.update_crawl_timestamp(sample_facility.facility_id)

        assert updated is not None
        assert updated.last_crawled_at is not None
        # Should be very recent
        assert (datetime.utcnow() - updated.last_crawled_at).seconds < 5

    def test_get_facilities_with_coordinates(self, test_session):
        """Test getting geocoded facilities."""
        repo = FacilityRepository(test_session)

        # Create facilities with and without coordinates
        for i in range(3):
            facility = Facility(
                exhibitor_name=f"Geocoded Facility {i}",
                usda_license=f"00-GEO-{i:04d}",
                state="TX",
                city="Geo City",
                coordinates='{"latitude": 29.7604, "longitude": -95.3698}'
            )
            repo.create(facility)

        for i in range(2):
            facility = Facility(
                exhibitor_name=f"Non-Geocoded Facility {i}",
                usda_license=f"00-NGO-{i:04d}",
                state="TX",
                city="Non-Geo City"
            )
            repo.create(facility)

        geocoded = repo.get_facilities_with_coordinates()

        assert len(geocoded) == 3
        assert all(f.coordinates is not None for f in geocoded)

    def test_get_states_with_facilities(self, test_session):
        """Test getting list of states with facilities."""
        repo = FacilityRepository(test_session)

        # Create facilities in different states
        states = ["TX", "FL", "CA", "TX", "NY", "FL"]
        for i, state in enumerate(states):
            facility = Facility(
                exhibitor_name=f"State Facility {i}",
                usda_license=f"00-STA-{i:04d}",
                state=state,
                city=f"City {i}"
            )
            repo.create(facility)

        # Create facility without state
        facility = Facility(
            exhibitor_name="No State Facility",
            usda_license="00-NST-0001",
            city="No State City"
        )
        repo.create(facility)

        unique_states = repo.get_states_with_facilities()

        assert len(unique_states) == 4  # TX, FL, CA, NY
        assert sorted(unique_states) == ["CA", "FL", "NY", "TX"]
