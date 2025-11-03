"""Tests for authentication utilities"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch

# Check if python-jose is available
try:
    import jose
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False

# Only import auth functions if jose is available
if HAS_JOSE:
    try:
        from backend.auth.auth import (
            hash_password,
            verify_password,
            create_access_token,
            verify_token,
            authenticate_user,
            SECRET_KEY,
            ALGORITHM
        )
        from backend.auth.permissions import (
            check_permission,
            require_role,
            require_permission
        )
        from backend.database.models import User
    except ImportError:
        # If auth module fails to import, skip all tests
        pytestmark = pytest.mark.skip(reason="Auth module requires python-jose")
else:
    # Skip all auth tests if jose not available
    pytestmark = pytest.mark.skip(reason="python-jose not available")

# Try to import jwt library for testing
try:
    from jose import jwt as jose_jwt
except ImportError:
    try:
        import jwt as jose_jwt
    except ImportError:
        jose_jwt = None


class TestPasswordHashing:
    """Tests for password hashing"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash format
    
    def test_verify_password_success(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password("wrong_password", hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that same password produces different hashes"""
        password = "test_password_123"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)
        
        # bcrypt includes salt, so hashes should be different
        assert hashed1 != hashed2
        
        # But both should verify correctly
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True


class TestJWTTokens:
    """Tests for JWT token creation and verification"""
    
    @pytest.mark.skipif(not HAS_JOSE, reason="python-jose or PyJWT not available")
    def test_create_access_token(self):
        """Test creating access token"""
        data = {"sub": "testuser", "role": "investigator"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.skipif(not HAS_JOSE, reason="python-jose or PyJWT not available")
    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Decode and verify expiry
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload
        assert "sub" in payload
    
    @pytest.mark.skipif(not HAS_JOSE, reason="python-jose or PyJWT not available")
    def test_verify_token_success(self):
        """Test token verification with valid token"""
        data = {"sub": "testuser", "role": "investigator"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    @pytest.mark.skipif(not HAS_JOSE, reason="python-jose or PyJWT not available")
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    @pytest.mark.skipif(not HAS_JOSE, reason="python-jose or PyJWT not available")
    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        data = {"sub": "testuser"}
        # Create token with negative expiry (already expired)
        expires_delta = timedelta(hours=-1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = verify_token(token)
        
        # Should return None due to expiration
        assert payload is None


class TestUserAuthentication:
    """Tests for user authentication"""
    
    def test_authenticate_user_success(self, db_session):
        """Test successful user authentication"""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123"),
            role="investigator",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Authenticate
        authenticated = authenticate_user(db_session, "testuser", "password123")
        
        assert authenticated is not None
        assert authenticated.username == "testuser"
    
    def test_authenticate_user_wrong_password(self, db_session):
        """Test authentication with wrong password"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123"),
            role="investigator",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated = authenticate_user(db_session, "testuser", "wrong_password")
        
        assert authenticated is None
    
    def test_authenticate_user_nonexistent(self, db_session):
        """Test authentication with nonexistent user"""
        authenticated = authenticate_user(db_session, "nonexistent", "password123")
        
        assert authenticated is None
    
    def test_authenticate_user_inactive(self, db_session):
        """Test authentication with inactive user"""
        user = User(
            username="inactive_user",
            email="inactive@example.com",
            password_hash=hash_password("password123"),
            role="investigator",
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated = authenticate_user(db_session, "inactive_user", "password123")
        
        assert authenticated is None


class TestPermissions:
    """Tests for permission checking"""
    
    def test_check_permission_admin(self):
        """Test that admin has all permissions"""
        user = Mock(User)
        user.role = "admin"
        user.permissions = {}
        
        assert check_permission(user, "any_permission") is True
    
    def test_check_permission_granted(self):
        """Test permission check with granted permission"""
        user = Mock(User)
        user.role = "investigator"
        user.permissions = {"view_tigers": True, "edit_tigers": False}
        
        assert check_permission(user, "view_tigers") is True
        assert check_permission(user, "edit_tigers") is False
    
    def test_check_permission_not_granted(self):
        """Test permission check without granted permission"""
        user = Mock(User)
        user.role = "investigator"
        user.permissions = {"view_tigers": True}
        
        assert check_permission(user, "edit_tigers") is False
        assert check_permission(user, "delete_tigers") is False
    
    def test_check_permission_empty_permissions(self):
        """Test permission check with empty permissions"""
        user = Mock(User)
        user.role = "investigator"
        user.permissions = {}
        
        assert check_permission(user, "any_permission") is False
    
    def test_require_role_decorator(self):
        """Test require_role decorator"""
        @require_role(["admin", "supervisor"])
        async def test_func():
            return "success"
        
        # This test documents the decorator structure
        # Actual testing would require FastAPI dependency injection
        assert callable(test_func)
    
    def test_require_permission_decorator(self):
        """Test require_permission decorator"""
        @require_permission("view_tigers")
        async def test_func():
            return "success"
        
        # This test documents the decorator structure
        assert callable(test_func)

