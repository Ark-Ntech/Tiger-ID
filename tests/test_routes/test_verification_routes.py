"""Tests for verification task API routes."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base, User, UserRole
from backend.auth.auth import hash_password, create_access_token
from datetime import timedelta


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
def db_session(test_engine):
    """Create a database session for testing."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_client(db_session):
    """Create a FastAPI test client."""
    from backend.api.app import create_app

    with patch('backend.api.app.AuditMiddleware'):
        app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from backend.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    app.user_middleware = []

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="verifier",
        email="verifier@example.com",
        password_hash=hash_password("TestPass123!"),
        role=UserRole.investigator.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers."""
    token = create_access_token(
        data={"sub": test_user.username, "role": test_user.role},
        expires_delta=timedelta(hours=1)
    )
    return {"Authorization": f"Bearer {token}"}


class TestGetVerificationTasks:
    """Tests for the get verification tasks endpoint."""

    def test_get_tasks_success(self, test_client, auth_headers):
        """Test getting verification tasks successfully."""
        response = test_client.get(
            "/api/v1/verification/tasks",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total"] == 0  # Empty list initially

    def test_get_tasks_no_auth(self, test_client):
        """Test getting tasks without authentication."""
        response = test_client.get("/api/v1/verification/tasks")

        assert response.status_code in [401, 403]

    def test_get_tasks_with_pagination(self, test_client, auth_headers):
        """Test pagination parameters."""
        response = test_client.get(
            "/api/v1/verification/tasks?page=1&page_size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 10

    def test_get_tasks_invalid_page(self, test_client, auth_headers):
        """Test with invalid page number."""
        response = test_client.get(
            "/api/v1/verification/tasks?page=0",
            headers=auth_headers
        )

        # Should return 422 for invalid parameter
        assert response.status_code == 422

    def test_get_tasks_invalid_page_size(self, test_client, auth_headers):
        """Test with page size exceeding maximum."""
        response = test_client.get(
            "/api/v1/verification/tasks?page_size=200",
            headers=auth_headers
        )

        # Should return 422 for page_size > 100
        assert response.status_code == 422

    def test_get_tasks_with_status_filter(self, test_client, auth_headers):
        """Test filtering by status."""
        response = test_client.get(
            "/api/v1/verification/tasks?status=pending",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_tasks_page_2(self, test_client, auth_headers):
        """Test getting second page."""
        response = test_client.get(
            "/api/v1/verification/tasks?page=2&page_size=20",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 2
