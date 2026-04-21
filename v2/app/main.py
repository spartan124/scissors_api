"""Scissors API v2 – FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .core.cache import close_redis, init_redis
from .core.config import get_settings
from .core.database import Base, engine
from .routers import auth, urls

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables, connect Redis. Shutdown: close connections."""
    # Create tables (Alembic handles this in prod; useful for dev/test)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await init_redis()
    yield
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Scissors API v2",
        description=(
            "High-performance URL shortening service built with FastAPI. "
            "Features Redis caching for sub-100 ms response times, async database "
            "access, background click tracking, QR code generation and analytics."
        ),
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth.router)
    app.include_router(urls.router)

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok", "version": "2.0.0"}

    return app


app = create_app()
