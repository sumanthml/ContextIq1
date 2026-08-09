import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

JWT_SECRET = getattr(settings, "SUPABASE_JWT_SECRET", "contextiq_jwt_super_secret_key_12345")
if not JWT_SECRET:
    JWT_SECRET = "contextiq_jwt_super_secret_key_12345"

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    salt = getattr(settings, "TENANT_SALT_KEY", "contextiq_salt_key_99")
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()

def create_access_token(user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=365) # Long lived session token
    
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def verify_user_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> str:
    """
    Validates the Bearer token header, decodes the JWT user ID payload,
    or falls back cleanly to the local session user token.
    """
    if not credentials:
        return "dev_local_tenant_user_123"
        
    token = credentials.credentials
    
    if not token or token == "dev_local_tenant_user_123":
        return "dev_local_tenant_user_123"
        
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM], options={"verify_aud": False})
        user_id = payload.get("sub")
        if user_id:
            return str(user_id)
    except Exception as e:
        # Fallback to direct token ID if simple string token is passed
        if isinstance(token, str) and len(token) > 0 and not token.startswith("eyJ"):
            return token
        print(f"⚠️ Token decode status: {e}")
        
    return "dev_local_tenant_user_123"

def get_tenant_vector_hash(user_id: str) -> str:
    """
    Converts a standard user_id into an isolated, salted cryptographic string
    to pass down to Qdrant payload filters.
    """
    salt_key = getattr(settings, "TENANT_SALT_KEY", "contextiq_secure_salt_shield_99")
    salted_string = f"{user_id}:{salt_key}"
    return hashlib.sha256(salted_string.encode()).hexdigest()