"""Repository for User data access."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import User, UserSession, UserRole
from backend.repositories.base import BaseRepository, PaginatedResult, FilterCriteria


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for UserSession data access."""

    def __init__(self, db: Session):
        super().__init__(db, UserSession)

    def get_active_sessions(self, user_id: UUID) -> List[UserSession]:
        """Get all active sessions for a user.

        Args:
            user_id: UUID of the user

        Returns:
            List of active UserSession objects
        """
        return (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            )
            .all()
        )

    def get_session_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Get session by ID if not expired.

        Args:
            session_id: UUID of the session

        Returns:
            UserSession if valid, None otherwise
        """
        return (
            self.db.query(UserSession)
            .filter(
                UserSession.session_id == session_id,
                UserSession.expires_at > datetime.utcnow()
            )
            .first()
        )

    def invalidate_user_sessions(self, user_id: UUID) -> int:
        """Invalidate all sessions for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Number of sessions invalidated
        """
        result = (
            self.db.query(UserSession)
            .filter(UserSession.user_id == user_id)
            .delete()
        )
        self.db.commit()
        return result

    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        result = (
            self.db.query(UserSession)
            .filter(UserSession.expires_at < datetime.utcnow())
            .delete()
        )
        self.db.commit()
        return result


class UserRepository(BaseRepository[User]):
    """Repository for User data access."""

    def __init__(self, db: Session):
        super().__init__(db, User)
        self.session_repo = UserSessionRepository(db)

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: UUID of the user

        Returns:
            User if found, None otherwise
        """
        return (
            self.db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username string

        Returns:
            User if found, None otherwise
        """
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: Email string

        Returns:
            User if found, None otherwise
        """
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role.

        Args:
            role: UserRole enum value

        Returns:
            List of User objects
        """
        return (
            self.db.query(User)
            .filter(User.role == role)
            .order_by(User.username)
            .all()
        )

    def get_active_users(self) -> List[User]:
        """Get all active users.

        Returns:
            List of active User objects
        """
        return (
            self.db.query(User)
            .filter(User.is_active == True)
            .order_by(User.username)
            .all()
        )

    def get_admins(self) -> List[User]:
        """Get all admin users.

        Returns:
            List of admin User objects
        """
        return self.get_by_role(UserRole.admin)

    def get_recently_logged_in(self, limit: int = 10) -> List[User]:
        """Get recently logged in users.

        Args:
            limit: Maximum number of results

        Returns:
            List of User objects
        """
        return (
            self.db.query(User)
            .filter(User.last_login.isnot(None))
            .order_by(desc(User.last_login))
            .limit(limit)
            .all()
        )

    def username_exists(self, username: str) -> bool:
        """Check if username already exists.

        Args:
            username: Username to check

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(
            self.db.query(User).filter(User.username == username).exists()
        ).scalar()

    def email_exists(self, email: str) -> bool:
        """Check if email already exists.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(
            self.db.query(User).filter(User.email == email).exists()
        ).scalar()

    def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp.

        Args:
            user_id: UUID of the user

        Returns:
            Updated User or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.last_login = datetime.utcnow()
        return self.update(user)

    def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """Deactivate a user account.

        Args:
            user_id: UUID of the user

        Returns:
            Updated User or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = False
        # Also invalidate all sessions
        self.session_repo.invalidate_user_sessions(user_id)
        return self.update(user)

    def activate_user(self, user_id: UUID) -> Optional[User]:
        """Activate a user account.

        Args:
            user_id: UUID of the user

        Returns:
            Updated User or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = True
        return self.update(user)

    def update_role(self, user_id: UUID, role: UserRole) -> Optional[User]:
        """Update user's role.

        Args:
            user_id: UUID of the user
            role: New role

        Returns:
            Updated User or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.role = role
        return self.update(user)

    def get_paginated_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        department: Optional[str] = None
    ) -> PaginatedResult[User]:
        """Get paginated users with common filters.

        Args:
            page: Page number
            page_size: Results per page
            role: Optional role filter
            is_active: Optional active status filter
            department: Optional department filter

        Returns:
            PaginatedResult with filtered users
        """
        filters = []
        if role:
            filters.append(FilterCriteria("role", "eq", role))
        if is_active is not None:
            filters.append(FilterCriteria("is_active", "eq", is_active))
        if department:
            filters.append(FilterCriteria("department", "eq", department))

        return self.get_paginated(
            page=page,
            page_size=page_size,
            sort_by="username",
            sort_order="asc",
            filters=filters if filters else None
        )

    # Session-related methods that delegate to session repository

    def get_active_sessions(self, user_id: UUID) -> List[UserSession]:
        """Get all active sessions for a user.

        Args:
            user_id: UUID of the user

        Returns:
            List of active UserSession objects
        """
        return self.session_repo.get_active_sessions(user_id)

    def create_session(self, session: UserSession) -> UserSession:
        """Create a new user session.

        Args:
            session: UserSession to create

        Returns:
            Created UserSession
        """
        return self.session_repo.create(session)

    def validate_session(self, session_id: UUID) -> Optional[UserSession]:
        """Validate a session by ID.

        Args:
            session_id: UUID of the session

        Returns:
            UserSession if valid, None otherwise
        """
        return self.session_repo.get_session_by_id(session_id)

    def invalidate_sessions(self, user_id: UUID) -> int:
        """Invalidate all sessions for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Number of sessions invalidated
        """
        return self.session_repo.invalidate_user_sessions(user_id)
