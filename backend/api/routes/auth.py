"""
Authentication API routes
"""

import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from utils.security import (
    verify_password,
    create_access_token,
    DEMO_USERS,
    get_current_user
)

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User information response"""
    username: str
    role: str
    user_id: int


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return JWT token
    
    Args:
        login_data: Username and password
        
    Returns:
        JWT access token and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    username = login_data.username.lower()
    
    # Check if user exists
    if username not in DEMO_USERS:
        logger.warning(f"Login attempt for non-existent user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    user = DEMO_USERS[username]
    
    # Verify password
    if not verify_password(login_data.password, user["password_hash"]):
        logger.warning(f"Failed login attempt for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": username, "role": user["role"]}
    )
    
    logger.info(f"Successful login for user: {username}")
    
    return LoginResponse(
        access_token=access_token,
        user={
            "username": username,
            "role": user["role"],
            "user_id": user["user_id"]
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Args:
        current_user: Injected by dependency
        
    Returns:
        Current user information
    """
    # Re-import here or move to top
    from utils.security import get_current_user as _
    
    return UserResponse(**current_user)


# Fix the dependency injection
from utils.security import get_current_user as get_current_user_dep

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user_dep)):
    """
    Get current authenticated user information
    """
    return UserResponse(**current_user)
