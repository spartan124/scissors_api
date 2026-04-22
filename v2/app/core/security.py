"""Password hashing and JWT helpers."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _make_token(data: dict[str, Any], expires_delta: Any) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire, "jti": secrets.token_urlsafe(16)})
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, email: str) -> str:
    return _make_token(
        {"sub": str(user_id), "email": email, "type": "access"},
        settings.JWT_ACCESS_TOKEN_EXPIRES,
    )


def create_refresh_token(user_id: int, email: str) -> str:
    return _make_token(
        {"sub": str(user_id), "email": email, "type": "refresh"},
        settings.JWT_REFRESH_TOKEN_EXPIRES,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and return the JWT payload.  Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
