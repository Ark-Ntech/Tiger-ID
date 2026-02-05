"""Tests for BaseRepository generic CRUD operations."""

import pytest
from uuid import uuid4
from backend.repositories.base import BaseRepository, PaginatedResult, FilterCriteria
from backend.database.models import Facility


class TestBaseRepository:
    """Tests for BaseRepository generic operations."""

    def test_get_by_id(self, db_session):
        """Test get_by_id retrieves entity correctly."""
        repo = BaseRepository(db_session, Facility)
        facility = Facility(exhibitor_name="Test", state="CA")
        created = repo.create(facility)
        retrieved = repo.get_by_id(created.facility_id)
        assert retrieved is not None
        assert retrieved.facility_id == created.facility_id

    def test_create(self, db_session):
        """Test create adds entity."""
        repo = BaseRepository(db_session, Facility)
        facility = Facility(exhibitor_name="New Facility", state="NY")
        created = repo.create(facility)
        assert created.facility_id is not None

    def test_update(self, db_session):
        """Test update modifies entity."""
        repo = BaseRepository(db_session, Facility)
        facility = Facility(exhibitor_name="Original")
        created = repo.create(facility)
        created.exhibitor_name = "Updated"
        updated = repo.update(created)
        assert updated.exhibitor_name == "Updated"

    def test_delete(self, db_session):
        """Test delete removes entity."""
        repo = BaseRepository(db_session, Facility)
        facility = Facility(exhibitor_name="To Delete")
        created = repo.create(facility)
        facility_id = created.facility_id
        result = repo.delete(created)
        assert result is True
        retrieved = repo.get_by_id(facility_id)
        assert retrieved is None
