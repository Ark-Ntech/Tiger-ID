"""Tests for authentication API routes."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base, User, UserRole, PasswordResetToken
from backend.auth.auth import hash_password, create_access_token
from datetime import datetime, timedelta


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

    # Clear middleware that may cause issues
    app.user_middleware = []

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("TestPass123!"),
        role=UserRole.investigator.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session):
    """Create an inactive test user."""
    user = User(
        username="inactiveuser",
        email="inactive@example.com",
        password_hash=hash_password("TestPass123!"),
        role=UserRole.investigator.value,
        is_active=False
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


class TestLogin:
    """Tests for login endpoint."""

    def test_login_success(self, test_client, test_user):
        """Test successful login."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
        assert "expires_in" in data

    def test_login_wrong_password(self, test_client, test_user):
        """Test login with wrong password."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, test_client):
        """Test login with non-existent user."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "TestPass123!"
            }
        )

        assert response.status_code == 401

    def test_login_remember_me(self, test_client, test_user):
        """Test login with remember_me flag."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPass123!",
                "remember_me": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Remember me should give longer expiry (7 days = 604800 seconds)
        assert data["expires_in"] == 604800

    def test_login_without_remember_me(self, test_client, test_user):
        """Test login without remember_me flag."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPass123!",
                "remember_me": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Default expiry should be shorter (ACCESS_TOKEN_EXPIRE_HOURS)
        assert data["expires_in"] < 604800


class TestRegister:
    """Tests for registration endpoint."""

    def test_register_success(self, test_client, db_session):
        """Test successful registration."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "user_id" in data
        assert "User registered successfully" in data["message"]

    def test_register_duplicate_username(self, test_client, test_user):
        """Test registration with existing username."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, test_client, test_user):
        """Test registration with existing email."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",  # Already exists
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_weak_password_too_short(self, test_client):
        """Test registration with short password."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "Abc1!"  # Too short
            }
        )

        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["detail"]

    def test_register_weak_password_no_uppercase(self, test_client):
        """Test registration with password missing uppercase."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "lowercase123!"
            }
        )

        assert response.status_code == 400
        assert "uppercase" in response.json()["detail"]

    def test_register_weak_password_no_lowercase(self, test_client):
        """Test registration with password missing lowercase."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "UPPERCASE123!"
            }
        )

        assert response.status_code == 400
        assert "lowercase" in response.json()["detail"]

    def test_register_weak_password_no_digit(self, test_client):
        """Test registration with password missing digit."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "NoDigitsHere!"
            }
        )

        assert response.status_code == 400
        assert "digit" in response.json()["detail"]

    def test_register_weak_password_no_special(self, test_client):
        """Test registration with password missing special character."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "NoSpecial123"
            }
        )

        assert response.status_code == 400
        assert "special character" in response.json()["detail"]

    def test_register_invalid_email(self, test_client):
        """Test registration with invalid email."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 422  # Validation error


class TestGetCurrentUser:
    """Tests for current user endpoint."""

    def test_get_current_user_success(self, test_client, test_user, auth_headers):
        """Test getting current user info."""
        response = test_client.get(
            "/api/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "user_id" in data

    def test_get_current_user_no_auth(self, test_client):
        """Test getting current user without auth."""
        response = test_client.get("/api/auth/me")

        assert response.status_code in [401, 403]

    def test_get_current_user_invalid_token(self, test_client):
        """Test getting current user with invalid token."""
        response = test_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, test_client, test_user, auth_headers):
        """Test successful logout."""
        response = test_client.post(
            "/api/auth/logout",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]

    def test_logout_no_auth(self, test_client):
        """Test logout without auth."""
        response = test_client.post("/api/auth/logout")

        assert response.status_code in [401, 403]


class TestVerifyToken:
    """Tests for token verification endpoint."""

    def test_verify_valid_token(self, test_client, test_user, auth_headers):
        """Test verifying a valid token."""
        response = test_client.post(
            "/api/auth/verify",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user"]["username"] == "testuser"

    def test_verify_invalid_token(self, test_client):
        """Test verifying an invalid token."""
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_verify_expired_token(self, test_client, test_user):
        """Test verifying an expired token."""
        # Create an expired token
        token = create_access_token(
            data={"sub": test_user.username, "role": test_user.role},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401


class TestPasswordReset:
    """Tests for password reset endpoints."""

    @patch('backend.api.auth_routes.get_email_service')
    def test_request_password_reset(self, mock_email_service, test_client, test_user):
        """Test requesting password reset."""
        mock_service = Mock()
        mock_service.send_password_reset_email = Mock()
        mock_email_service.return_value = mock_service

        response = test_client.post(
            "/api/auth/password-reset/request",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        # Should always return success message (security)
        assert "password reset link" in response.json()["message"].lower()

    def test_request_password_reset_nonexistent_email(self, test_client):
        """Test password reset with non-existent email."""
        response = test_client.post(
            "/api/auth/password-reset/request",
            json={"email": "nonexistent@example.com"}
        )

        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "password reset link" in response.json()["message"].lower()

    def test_confirm_password_reset(self, test_client, test_user, db_session):
        """Test confirming password reset."""
        # Create a reset token
        reset_token = PasswordResetToken(
            user_id=test_user.user_id,
            token="valid_reset_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(reset_token)
        db_session.commit()

        response = test_client.post(
            "/api/auth/password-reset/confirm",
            json={
                "token": "valid_reset_token",
                "new_password": "NewSecurePass123!"
            }
        )

        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]

    def test_confirm_password_reset_invalid_token(self, test_client):
        """Test password reset with invalid token."""
        response = test_client.post(
            "/api/auth/password-reset/confirm",
            json={
                "token": "invalid_token",
                "new_password": "NewSecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_confirm_password_reset_expired_token(self, test_client, test_user, db_session):
        """Test password reset with expired token."""
        # Create an expired reset token
        reset_token = PasswordResetToken(
            user_id=test_user.user_id,
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        db_session.add(reset_token)
        db_session.commit()

        response = test_client.post(
            "/api/auth/password-reset/confirm",
            json={
                "token": "expired_token",
                "new_password": "NewSecurePass123!"
            }
        )

        assert response.status_code == 400

    def test_confirm_password_reset_weak_password(self, test_client, test_user, db_session):
        """Test password reset with weak new password."""
        # Create a valid reset token
        reset_token = PasswordResetToken(
            user_id=test_user.user_id,
            token="valid_token_weak",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(reset_token)
        db_session.commit()

        response = test_client.post(
            "/api/auth/password-reset/confirm",
            json={
                "token": "valid_token_weak",
                "new_password": "weak"  # Too weak
            }
        )

        assert response.status_code == 400
        # Should mention password requirements
        assert "Password must" in response.json()["detail"]

    def test_confirm_password_reset_used_token(self, test_client, test_user, db_session):
        """Test password reset with already used token."""
        # Create a used reset token
        reset_token = PasswordResetToken(
            user_id=test_user.user_id,
            token="used_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used_at=datetime.utcnow()
        )
        db_session.add(reset_token)
        db_session.commit()

        response = test_client.post(
            "/api/auth/password-reset/confirm",
            json={
                "token": "used_token",
                "new_password": "NewSecurePass123!"
            }
        )

        assert response.status_code == 400


class TestPasswordValidation:
    """Tests for password validation function."""

    def test_validate_password_strength_valid(self):
        """Test validation of a valid password."""
        from backend.api.auth_routes import validate_password_strength

        errors = validate_password_strength("SecurePass123!")

        assert len(errors) == 0

    def test_validate_password_strength_all_requirements(self):
        """Test validation catches all issues."""
        from backend.api.auth_routes import validate_password_strength

        errors = validate_password_strength("abc")

        # Should have multiple errors
        assert len(errors) > 0
        assert any("8 characters" in e for e in errors)
        assert any("uppercase" in e for e in errors)
        assert any("digit" in e for e in errors)
        assert any("special" in e for e in errors)
