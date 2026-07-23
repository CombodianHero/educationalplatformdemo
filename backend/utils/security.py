"""
Security utilities for JWT authentication and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from utils.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Demo users for PoC
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": pwd_context.hash("admin123"),
        "role": "admin",
        "user_id": 1
    },
    "student": {
        "username": "student",
        "password_hash": pwd_context.hash("student123"),
        "role": "student",
        "user_id": 2
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm="HS256"
    )
    
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Extract and validate current user from JWT token
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User data dictionary
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        username: str = payload.get("sub")
        
        if username is None or username not in DEMO_USERS:
            raise credentials_exception
        
        user_data = DEMO_USERS[username].copy()
        user_data.pop("password_hash")  # Don't expose password hash
        
        return user_data
        
    except JWTError:
        raise credentials_exception


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """
    Verify that the current user has admin role
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User data if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
