"""Authentication routes: signup, login, refresh, logout, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import blacklist_token, is_token_blacklisted
from ..core.config import get_settings
from ..core.database import get_db
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ..dependencies import bearer_scheme, get_current_user, get_refresh_user
from ..models.user import User
from ..schemas.user import (
    AccessTokenResponse,
    LoginRequest,
    TokenResponse,
    UserOut,
    UserSignUp,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignUp, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user account."""
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="A user with that username already exists!")

    email_check = await db.execute(select(User).where(User.email == payload.email))
    if email_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="A user with that email already exists!")

    user = User(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Authenticate user and return JWT access + refresh tokens."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials. Check credentials and try again.",
        )

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "username": user.username,
    }


@router.post("/refresh", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
async def refresh(
    user_and_payload: tuple = Depends(get_refresh_user),
) -> dict:
    """Issue a new access token using a valid refresh token."""
    user, _ = user_and_payload
    access_token = create_access_token(user.id, user.email)
    return {"access_token": access_token}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    credentials=Depends(bearer_scheme),
) -> dict:
    """Blacklist the current access token."""
    from jose import JWTError

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    jti: str | None = payload.get("jti")
    if jti:
        exp = payload.get("exp", 0)
        import time

        ttl = max(int(exp - time.time()), 1)
        await blacklist_token(jti, ttl)

    return {"message": "Logged out successfully!"}


@router.get("/user", response_model=UserOut)
async def get_user(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user's profile."""
    return current_user
