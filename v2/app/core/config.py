"""Application settings loaded from environment variables."""
from datetime import timedelta
from functools import lru_cache

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "dev"
    SECRET_KEY: str = "changeme"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./scissors_v2.db"

    # JWT
    JWT_SECRET_KEY: str = "changeme-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=120)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(hours=272)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_REDIRECT: int = 300   # seconds – redirect lookup (hot path)
    CACHE_TTL_SHORT: int = 30       # seconds – short-lived caches
    CACHE_TTL_LONG: int = 60        # seconds – medium-lived caches

    # Rate limiting
    RATE_LIMIT_DEFAULT: str = "1000/day;50/hour"
    RATE_LIMIT_WRITE: str = "5/second"
    RATE_LIMIT_READ: str = "50/second"

    # GeoIP (optional – gracefully skipped when key absent)
    GEOIPIFY_API_KEY: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _coerce_postgres(cls, v: str) -> str:
        # Heroku-style postgres:// → postgresql+asyncpg://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
