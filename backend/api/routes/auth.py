from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.security import DEMO_USERS, verify_password, create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(data: LoginRequest):
    username = data.username.lower().strip()
    password = data.password.strip()
    if username not in DEMO_USERS:
        raise HTTPException(401, detail="Invalid credentials")
    user = DEMO_USERS[username]
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(401, detail="Invalid credentials")
    token = create_access_token({"sub": username, "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"username": username, "role": user["role"], "user_id": user["user_id"]}
    }
