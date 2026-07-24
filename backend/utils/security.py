"""
Simple secure password hashing (SHA256) + JWT
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)

def hash_password(password: str) -> str:
    """One-way hash using SHA256 with a fixed salt (PoC only)."""
    salt = "edu_platform_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Demo users (passwords: admin123, student123)
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": hash_password("admin123"),
        "role": "admin",
        "user_id": 1
    },
    "student": {
        "username": "student",
        "password_hash": hash_password("student123"),
        "role": "student",
        "user_id": 2
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username not in DEMO_USERS:
            raise HTTPException(status_code=401, detail="User not found")
        user = DEMO_USERS[username].copy()
        user.pop("password_hash", None)
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
