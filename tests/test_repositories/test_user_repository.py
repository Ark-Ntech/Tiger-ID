"""Tests for UserRepository and UserSessionRepository classes."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base, User, UserSession, UserRole
from backend.repositories.user_repository import UserRepository, UserSessionRepository


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
        username="testuser",
        email="test@example.com",
        password_hash="hashedpassword123",
        role=UserRole.investigator.value,
        is_active=True
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


class TestUserSessionRepository:
    """Tests for UserSessionRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = UserSessionRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == UserSession

    def test_get_active_sessions(self, test_session, sample_user):
        """Test getting active sessions for a user."""
        repo = UserSessionRepository(test_session)

        # Create active sessions
        for i in range(3):
            session = UserSession(
                user_id=sample_user.user_id,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            repo.create(session)

        # Create expired session
        expired_session = UserSession(
            user_id=sample_user.user_id,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        repo.create(expired_session)

        active = repo.get_active_sessions(sample_user.user_id)

        assert len(active) == 3
        assert all(s.expires_at > datetime.utcnow() for s in active)

    def test_get_session_by_id_valid(self, test_session, sample_user):
        """Test getting a valid session by ID."""
        repo = UserSessionRepository(test_session)

        session = UserSession(
            user_id=sample_user.user_id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        created = repo.create(session)

        found = repo.get_session_by_id(created.session_id)

        assert found is not None
        assert found.session_id == created.session_id

    def test_get_session_by_id_expired(self, test_session, sample_user):
        """Test getting an expired session returns None."""
        repo = UserSessionRepository(test_session)

        session = UserSession(
            user_id=sample_user.user_id,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        created = repo.create(session)

        found = repo.get_session_by_id(created.session_id)

        assert found is None

    def test_invalidate_user_sessions(self, test_session, sample_user):
        """Test invalidating all sessions for a user."""
        repo = UserSessionRepository(test_session)

        # Create multiple sessions
        for i in range(5):
            session = UserSession(
                user_id=sample_user.user_id,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            repo.create(session)

        # Invalidate all
        count = repo.invalidate_user_sessions(sample_user.user_id)

        assert count == 5

        # Verify no sessions remain
        remaining = repo.get_active_sessions(sample_user.user_id)
        assert len(remaining) == 0

    def test_cleanup_expired_sessions(self, test_session, sample_user):
        """Test cleaning up expired sessions."""
        repo = UserSessionRepository(test_session)

        # Create active sessions
        for i in range(2):
            session = UserSession(
                user_id=sample_user.user_id,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            repo.create(session)

        # Create expired sessions
        for i in range(3):
            session = UserSession(
                user_id=sample_user.user_id,
                expires_at=datetime.utcnow() - timedelta(hours=i + 1)
            )
            repo.create(session)

        # Cleanup
        removed = repo.cleanup_expired_sessions()

        assert removed == 3

        # Verify only active sessions remain
        remaining = test_session.query(UserSession).filter(
            UserSession.user_id == sample_user.user_id
        ).all()
        assert len(remaining) == 2


class TestUserRepository:
    """Tests for UserRepository class."""

    def test_repository_initialization(self, test_session):
        """Test repository initialization."""
        repo = UserRepository(test_session)
        assert repo.db == test_session
        assert repo.model_class == User
        assert repo.session_repo is not None

    def test_get_by_id(self, test_session, sample_user):
        """Test getting user by ID."""
        repo = UserRepository(test_session)

        found = repo.get_by_id(sample_user.user_id)

        assert found is not None
        assert found.user_id == sample_user.user_id
        assert found.username == "testuser"

    def test_get_by_id_not_found(self, test_session):
        """Test getting user by non-existent ID."""
        repo = UserRepository(test_session)

        found = repo.get_by_id(uuid4())

        assert found is None

    def test_get_by_username(self, test_session, sample_user):
        """Test getting user by username."""
        repo = UserRepository(test_session)

        found = repo.get_by_username("testuser")

        assert found is not None
        assert found.username == "testuser"

    def test_get_by_username_not_found(self, test_session):
        """Test getting user by non-existent username."""
        repo = UserRepository(test_session)

        found = repo.get_by_username("nonexistent")

        assert found is None

    def test_get_by_email(self, test_session, sample_user):
        """Test getting user by email."""
        repo = UserRepository(test_session)

        found = repo.get_by_email("test@example.com")

        assert found is not None
        assert found.email == "test@example.com"

    def test_get_by_role(self, test_session):
        """Test getting users by role."""
        repo = UserRepository(test_session)

        # Create users with different roles
        roles = [UserRole.investigator, UserRole.analyst, UserRole.investigator, UserRole.admin]
        for i, role in enumerate(roles):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash="hashedpassword",
                role=role.value,
                is_active=True
            )
            repo.create(user)

        investigators = repo.get_by_role(UserRole.investigator)

        assert len(investigators) == 2
        assert all(u.role == UserRole.investigator.value for u in investigators)

    def test_get_active_users(self, test_session):
        """Test getting active users."""
        repo = UserRepository(test_session)

        # Create active users
        for i in range(3):
            user = User(
                username=f"active{i}",
                email=f"active{i}@example.com",
                password_hash="hashedpassword",
                role=UserRole.investigator.value,
                is_active=True
            )
            repo.create(user)

        # Create inactive users
        for i in range(2):
            user = User(
                username=f"inactive{i}",
                email=f"inactive{i}@example.com",
                password_hash="hashedpassword",
                role=UserRole.analyst.value,
                is_active=False
            )
            repo.create(user)

        active = repo.get_active_users()

        assert len(active) == 3
        assert all(u.is_active for u in active)

    def test_get_admins(self, test_session):
        """Test getting admin users."""
        repo = UserRepository(test_session)

        # Create admin users
        for i in range(2):
            user = User(
                username=f"admin{i}",
                email=f"admin{i}@example.com",
                password_hash="hashedpassword",
                role=UserRole.admin.value,
                is_active=True
            )
            repo.create(user)

        # Create non-admin
        user = User(
            username="regular",
            email="regular@example.com",
            password_hash="hashedpassword",
            role=UserRole.investigator.value,
            is_active=True
        )
        repo.create(user)

        admins = repo.get_admins()

        assert len(admins) == 2
        assert all(u.role == UserRole.admin.value for u in admins)

    def test_get_recently_logged_in(self, test_session):
        """Test getting recently logged in users."""
        repo = UserRepository(test_session)

        now = datetime.utcnow()
        # Create users with different last_login times
        for i in range(5):
            user = User(
                username=f"recent{i}",
                email=f"recent{i}@example.com",
                password_hash="hashedpassword",
                role=UserRole.investigator.value,
                is_active=True,
                last_login=now - timedelta(hours=i)
            )
            repo.create(user)

        # Create user without last_login
        user = User(
            username="neverlogged",
            email="never@example.com",
            password_hash="hashedpassword",
            role=UserRole.investigator.value,
            is_active=True
        )
        repo.create(user)

        recent = repo.get_recently_logged_in(limit=3)

        assert len(recent) == 3
        assert recent[0].username == "recent0"  # Most recent
        assert recent[1].username == "recent1"
        assert recent[2].username == "recent2"

    def test_username_exists(self, test_session, sample_user):
        """Test checking if username exists."""
        repo = UserRepository(test_session)

        assert repo.username_exists("testuser") is True
        assert repo.username_exists("nonexistent") is False

    def test_email_exists(self, test_session, sample_user):
        """Test checking if email exists."""
        repo = UserRepository(test_session)

        assert repo.email_exists("test@example.com") is True
        assert repo.email_exists("nonexistent@example.com") is False

    def test_update_last_login(self, test_session, sample_user):
        """Test updating user's last login timestamp."""
        repo = UserRepository(test_session)

        # Initially no last_login
        assert sample_user.last_login is None

        updated = repo.update_last_login(sample_user.user_id)

        assert updated is not None
        assert updated.last_login is not None
        # Should be very recent
        assert (datetime.utcnow() - updated.last_login).seconds < 5

    def test_update_last_login_not_found(self, test_session):
        """Test updating last login for non-existent user."""
        repo = UserRepository(test_session)

        result = repo.update_last_login(uuid4())

        assert result is None

    def test_deactivate_user(self, test_session, sample_user):
        """Test deactivating a user."""
        repo = UserRepository(test_session)

        # Create a session for the user
        session = UserSession(
            user_id=sample_user.user_id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        repo.session_repo.create(session)

        # Deactivate
        updated = repo.deactivate_user(sample_user.user_id)

        assert updated is not None
        assert updated.is_active is False

        # Sessions should be invalidated
        sessions = repo.session_repo.get_active_sessions(sample_user.user_id)
        assert len(sessions) == 0

    def test_activate_user(self, test_session):
        """Test activating a user."""
        repo = UserRepository(test_session)

        # Create inactive user
        user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash="hashedpassword",
            role=UserRole.investigator.value,
            is_active=False
        )
        created = repo.create(user)

        # Activate
        updated = repo.activate_user(created.user_id)

        assert updated is not None
        assert updated.is_active is True

    def test_update_role(self, test_session, sample_user):
        """Test updating user's role."""
        repo = UserRepository(test_session)

        assert sample_user.role == UserRole.investigator.value

        updated = repo.update_role(sample_user.user_id, UserRole.admin)

        assert updated is not None
        assert updated.role == UserRole.admin.value

    def test_get_paginated_with_filters(self, test_session):
        """Test paginated results with filters."""
        repo = UserRepository(test_session)

        # Create users with different attributes
        for i in range(5):
            user = User(
                username=f"pagtest{i}",
                email=f"pagtest{i}@example.com",
                password_hash="hashedpassword",
                role=UserRole.investigator.value if i < 3 else UserRole.analyst.value,
                is_active=i < 4,
                department="Engineering" if i < 2 else "Research"
            )
            repo.create(user)

        # Filter by role
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            role=UserRole.investigator
        )
        assert result.total == 3

        # Filter by active status
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            is_active=True
        )
        assert result.total == 4

        # Filter by department
        result = repo.get_paginated_with_filters(
            page=1,
            page_size=20,
            department="Engineering"
        )
        assert result.total == 2

    def test_create_session(self, test_session, sample_user):
        """Test creating a session via user repository."""
        repo = UserRepository(test_session)

        session = UserSession(
            user_id=sample_user.user_id,
            expires_at=datetime.utcnow() + timedelta(hours=2)
        )

        created = repo.create_session(session)

        assert created.session_id is not None
        assert created.user_id == sample_user.user_id

    def test_validate_session(self, test_session, sample_user):
        """Test validating a session."""
        repo = UserRepository(test_session)

        # Create a valid session
        session = UserSession(
            user_id=sample_user.user_id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        created = repo.create_session(session)

        # Validate
        validated = repo.validate_session(created.session_id)

        assert validated is not None
        assert validated.session_id == created.session_id

    def test_invalidate_sessions(self, test_session, sample_user):
        """Test invalidating all sessions for a user."""
        repo = UserRepository(test_session)

        # Create sessions
        for i in range(3):
            session = UserSession(
                user_id=sample_user.user_id,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            repo.create_session(session)

        # Invalidate all
        count = repo.invalidate_sessions(sample_user.user_id)

        assert count == 3

        # Verify
        active = repo.get_active_sessions(sample_user.user_id)
        assert len(active) == 0
