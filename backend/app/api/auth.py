import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from app.services.db_service import get_user_by_email, get_user_by_id, save_user
from app.core.security import hash_password, create_access_token, verify_user_token

router = APIRouter(prefix="/auth", tags=["User Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    status: str
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/register", response_model=AuthResponse)
async def register_user(payload: RegisterRequest):
    email = payload.email.lower().strip()
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty.")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
        
    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")
        
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    hashed_pwd = hash_password(payload.password)
    
    new_user = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": email,
        "password": hashed_pwd,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    save_user(new_user)
    
    token = create_access_token(user_id=user_id, email=email)
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": new_user["name"],
            "email": new_user["email"],
            "created_at": new_user["created_at"]
        }
    }

@router.post("/login", response_model=AuthResponse)
async def login_user(payload: LoginRequest):
    email = payload.email.lower().strip()
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    hashed_input = hash_password(payload.password)
    if user.get("password") != hashed_input:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    token = create_access_token(user_id=user["id"], email=user["email"])
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user.get("name", "User"),
            "email": user["email"],
            "created_at": user.get("created_at")
        }
    }

@router.get("/me")
async def get_current_user_profile(current_user_id: str = Depends(verify_user_token)):
    user = get_user_by_id(current_user_id)
    if user:
        return {
            "id": user["id"],
            "name": user.get("name", "User"),
            "email": user["email"],
            "created_at": user.get("created_at")
        }
    return {
        "id": current_user_id,
        "name": "Developer Workspace User",
        "email": "dev@contextiq.local",
        "created_at": "2026-08-09T00:00:00Z"
    }
