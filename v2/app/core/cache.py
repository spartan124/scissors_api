"""Redis connection pool and cache helpers."""
from __future__ import annotations

import logging
from typing import Any

import redis.asyncio as aioredis

from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def init_redis() -> None:
    global _redis
    _redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis has not been initialised. Call init_redis() first.")
    return _redis


# --------------------------------------------------------------------------- #
# Thin cache helpers                                                           #
# --------------------------------------------------------------------------- #

async def cache_get(key: str) -> str | None:
    try:
        return await get_redis().get(key)
    except Exception as exc:
        logger.warning("cache_get failed: %s", exc)
        return None


async def cache_set(key: str, value: str, ttl: int) -> None:
    try:
        await get_redis().setex(key, ttl, value)
    except Exception as exc:
        logger.warning("cache_set failed: %s", exc)


async def cache_delete(key: str) -> None:
    try:
        await get_redis().delete(key)
    except Exception as exc:
        logger.warning("cache_delete failed: %s", exc)


# Token blacklist helpers
async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT JTI to the blacklist."""
    await cache_set(f"blacklist:{jti}", "1", ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    """Return True if the token's JTI is in the blacklist."""
    val = await cache_get(f"blacklist:{jti}")
    return val is not None
