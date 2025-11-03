"""Permission and role checking utilities"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.database import User
from backend.auth.auth import get_current_user


def check_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission"""
    if user.role == "admin":
        return True
    
    user_permissions = user.permissions or {}
    return user_permissions.get(permission, False)


def require_role(allowed_roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(func):
        async def wrapper(
            current_user: User = get_current_user,
            *args,
            **kwargs
        ):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {allowed_roles}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(
            current_user: User = get_current_user,
            *args,
            **kwargs
        ):
            if not check_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required permission: {permission}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

