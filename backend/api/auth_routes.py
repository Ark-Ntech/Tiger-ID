"""Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
import secrets
from datetime import datetime, timedelta

from backend.database import get_db, User
from backend.database.models import PasswordResetToken
from backend.config.settings import get_settings

from backend.auth.auth import (
    authenticate_user,
    create_access_token,
    hash_password,
    get_current_user as get_current_user_dependency,
    ACCESS_TOKEN_EXPIRE_HOURS
)
from backend.utils.email import get_email_service

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    user: dict
    expires_in: int


class RegisterRequest(BaseModel):
    """User registration request model"""
    username: str
    email: EmailStr
    password: str
    role: str = "investigator"
    full_name: Optional[str] = None


class RegisterResponse(BaseModel):
    """Registration response model"""
    user_id: str
    username: str
    email: str
    message: str


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
async def login_endpoint(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token
    
    Args:
        login_data: Login credentials
        db: Database session
    
    Returns:
        JWT token and user information
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with appropriate expiry
    expires_delta = timedelta(days=7) if login_data.remember_me else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    # Convert role enum to string for JWT serialization
    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
    token_data = {"sub": user.username, "role": role_value}
    access_token = create_access_token(token_data, expires_delta=expires_delta)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "permissions": user.permissions or {}
        },
        expires_in=int(expires_delta.total_seconds())
    )


@router.post("/register", response_model=RegisterResponse)
async def register_endpoint(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    Args:
        register_data: Registration information
        db: Database session
    
    Returns:
        Created user information
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == register_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == register_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(register_data.password)
    new_user = User(
        username=register_data.username,
        email=register_data.email,
        password_hash=hashed_password,
        role=register_data.role,
        is_active=True,
        full_name=register_data.full_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RegisterResponse(
        user_id=str(new_user.user_id),
        username=new_user.username,
        email=new_user.email,
        message="User registered successfully"
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current authenticated user from dependency
    
    Returns:
        User information
    """
    return {
        "user_id": str(current_user.user_id),
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "permissions": current_user.permissions or {},
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.post("/logout")
async def logout_endpoint(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Logout endpoint (token invalidation handled client-side)
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    # In a production system, you might want to blacklist tokens
    # For now, logout is handled client-side by discarding the token
    return {"message": "Logged out successfully"}


@router.post("/verify")
async def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Verify if a token is valid
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
    
    Returns:
        Token validity and user information
    """
    from backend.auth.auth import verify_token
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {
        "valid": True,
        "user": {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }


@router.post("/password-reset/request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset (sends email with reset link)
    
    Args:
        reset_request: Password reset request with email
        db: Database session
        
    Returns:
        Success message (always returns success for security)
    """
    # Find user by email
    user = db.query(User).filter(User.email == reset_request.email).first()
    
    # Always return success to prevent email enumeration
    if not user or not user.is_active:
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Create or update reset token
    existing_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if existing_token:
        # Update existing token
        existing_token.token = reset_token
        existing_token.expires_at = expires_at
    else:
        # Create new token
        reset_token_record = PasswordResetToken(
            user_id=user.user_id,
            token=reset_token,
            expires_at=expires_at
        )
        db.add(reset_token_record)
    
    db.commit()
    
    # Send email with reset link
    # In production, this would be the actual frontend URL
    settings = get_settings()
    frontend_url = settings.frontend_url
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    email_service = get_email_service()
    email_service.send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        reset_url=reset_url
    )
    
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token
    
    Args:
        reset_confirm: Password reset confirmation with token and new password
        db: Database session
        
    Returns:
        Success message
    """
    # Find valid reset token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_confirm.token,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate password
    if len(reset_confirm.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Update user password
    user = db.query(User).filter(User.user_id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.password_hash = hash_password(reset_confirm.new_password)
    
    # Mark token as used
    reset_token.used_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password reset successfully"}

