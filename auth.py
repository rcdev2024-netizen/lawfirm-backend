import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import supabase

SECRET_KEY = os.getenv("SECRET_KEY", "atty-rochelle-secret-key-change-in-production-2024")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _normalize_user(user: dict) -> dict:
    """
    Flatten the joined roles row so that current_user["role"] always returns
    the role name string (e.g. "admin", "attorney") regardless of whether the
    data came from a join or a plain select.
    """
    if "roles" in user and isinstance(user["roles"], dict):
        user["role"] = user["roles"].get("name", "client")
        del user["roles"]
    elif "role_id" in user and "role" not in user:
        user["role"] = "client"
    return user


def _get_user_from_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
        # Join roles so we always get the role name alongside role_id
        result = (
            supabase.table("users")
            .select("*, roles!users_role_id_fkey(name)")
            .eq("email", email)
            .execute()
        )
        if not result.data:
            return None
        return _normalize_user(result.data[0])
    except JWTError:
        return None


def get_role_id(role_name: str) -> Optional[int]:
    """Look up a role's primary-key id by its name slug."""
    result = (
        supabase.table("roles")
        .select("id")
        .eq("name", role_name)
        .eq("is_active", True)
        .execute()
    )
    return result.data[0]["id"] if result.data else None


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = _get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    if not token:
        return None
    return _get_user_from_token(token)


def require_role(*allowed_roles: str):
    """
    Dependency factory — use as:
        Depends(require_role("admin", "attorney"))
    """
    def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to: {', '.join(allowed_roles)}"
            )
        return current_user
    return _check
