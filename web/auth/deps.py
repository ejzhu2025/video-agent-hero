"""auth/deps.py — JWT helpers and FastAPI current_user dependency."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt

from web.auth.models import User, get_user

# ── Config (set via env vars) ─────────────────────────────────────────────────
# Generate a strong random secret: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_generate_with_secrets_token_hex_32")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30
COOKIE_NAME = "vah_session"


# ── Token helpers ─────────────────────────────────────────────────────────────

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> Optional[str]:
    """Returns user_id (sub) or None if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ── FastAPI dependency ────────────────────────────────────────────────────────

def current_user(vah_session: Optional[str] = Cookie(default=None)) -> User:
    """Dependency: returns authenticated User or raises 401."""
    if not vah_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    user_id = decode_token(vah_session)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    user = get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def optional_user(vah_session: Optional[str] = Cookie(default=None)) -> Optional[User]:
    """Like current_user but returns None instead of raising (for public routes)."""
    if not vah_session:
        return None
    user_id = decode_token(vah_session)
    if not user_id:
        return None
    return get_user(user_id)
