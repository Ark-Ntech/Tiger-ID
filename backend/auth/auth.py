"""Authentication utilities"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from backend.database import get_db, User
from backend.config.settings import get_settings

settings = get_settings()

# HTTP Bearer security
security = HTTPBearer()

# JWT settings
SECRET_KEY = settings.authentication.jwt_secret_key
ALGORITHM = settings.authentication.jwt_algorithm
ACCESS_TOKEN_EXPIRE_HOURS = settings.authentication.jwt_expiration_hours


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly"""
    # Convert password to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash"""
    # Convert both to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login_user(db: Session, username: str, password: str, remember_me: bool = False) -> Optional[dict]:
    """
    Login user and return user data with token
    
    Args:
        db: Database session
        username: Username
        password: Password
        remember_me: If True, token lasts 7 days, else 24 hours
        
    Returns:
        Dict with user info and token, or None if authentication fails
    """
    user = authenticate_user(db, username, password)
    if not user:
        return None
    
    # Create token
    expires_delta = timedelta(days=7) if remember_me else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
    token_data = {"sub": user.username, "role": role_value}
    access_token = create_access_token(token_data, expires_delta=expires_delta)
    
    return {
        "token": access_token,
        "user": {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "role": role_value,
            "permissions": user.permissions or {}
        }
    }


def verify_token(token: str, db: Session) -> Optional[User]:
    """
    Verify a token and return User object
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object if token is valid, None otherwise
    """
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user"""
    token = credentials.credentials
    
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_current_user_ws(token: str, db: Session) -> Optional[User]:
    """Get the current authenticated user from WebSocket token"""
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = db.query(User).filter(User.username == username).first()
        return user
    except:
        return None
