# Changelog

All notable changes to **Scissors API** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project adheres to [Semantic Versioning](https://semver.org/).

---

## [2.0.0] — 2026-04-21

Complete rebuild of the URL shortening service as a FastAPI application (`v2/`).  
The original Flask implementation (`api/`) is preserved unchanged.

### Added

#### Framework & performance
- **FastAPI** replaces Flask + Flask-RESTX for full async ASGI request handling.
- **uvicorn[standard]** with multiple worker support via `Procfile` / Docker.
- **Async SQLAlchemy 2.0** (`mapped_column` declarative style) with `asyncpg` driver for PostgreSQL and `aiosqlite` for local/test use.
- **Redis** caching layer replacing the in-process `SimpleCache`:
  - Redirect hot path cached at `CACHE_TTL_REDIRECT` (default 300 s) — resolves in ~0.5 ms with zero DB queries.
  - URL lookups, history, analytics, and QR codes individually cached and invalidated on delete.
- **BackgroundTasks** for non-blocking click recording — the 302 redirect is returned before any DB write occurs.
- Connection pooling: SQLAlchemy pool (10 core + 20 overflow) and Redis pool (50 connections).
- Database indexes on `short_code`, `user_id`, `email`, `username`.

#### Security
- `jti` (JWT ID) claim added to every token, enabling per-token blacklisting on logout.
- `secrets.choice` replaces `random.choices` for cryptographically secure short code generation.
- Custom short codes validated with a regex (`[A-Za-z0-9_-]{3,20}`).
- Short code collision loop raises `HTTP 503` rather than silently reusing a conflicting code.
- `passlib[bcrypt]` for password hashing (unchanged algorithm, new library wrapper).
- `python-jose[cryptography]` 3.4.0+ for JWT (fixes ECDSA algorithm-confusion CVE).

#### API endpoints
- `POST /auth/signup` — register a new user.
- `POST /auth/login` — returns JWT access + refresh tokens.
- `POST /auth/refresh` — issue a new access token via refresh token.
- `POST /auth/logout` — blacklist current token in Redis.
- `GET  /auth/user` — authenticated user profile.
- `POST /shorten` — shorten a URL; returns `shortened_url` + `short_code`.
- `GET  /{short_code}` — redirect (302) to original URL.
- `GET  /shortened/{short_code}` — return the full shortened URL string.
- `DELETE /shortened/{short_code}` — delete a URL (owner only).
- `GET  /{short_code}/qrcode` — PNG QR code (seagreen on white, cached).
- `GET  /analytics/{short_code}` — JSON click analytics (`total_clicks`, `clicks_by_source`).
- `GET  /analytics/{short_code}/chart` — PNG bar chart of clicks per source location.
- `GET  /history` — all short URLs for the current user.
- `GET  /health` — health check endpoint.

#### Tooling & deployment
- **Pydantic v2** request/response schemas with `model_config = {"from_attributes": True}`.
- **pydantic-settings** for typed, validated configuration from environment variables.
- **Alembic** async migration environment (`alembic/env.py`).
- **SlowAPI** rate limiting per IP address.
- `Dockerfile` — multi-stage build, non-root user, production-ready.
- `docker-compose.yml` — app + `postgres:16-alpine` + `redis:7-alpine` with health checks.
- `.env.example` — full environment variable template.
- `render.yaml` — Render platform blueprint for one-click deployment.
- `pytest.ini` with `asyncio_mode = auto`.
- Full `pytest-asyncio` test suite (22 tests).

### Changed

- **Database driver**: `psycopg2` (sync) → `asyncpg` (async, non-blocking).
- **Cache backend**: Flask-Caching `SimpleCache` (in-process) → Redis (distributed, persistent).
- **Token blacklist**: in-process `SimpleCache` → Redis (survives restarts, works across workers).
- **Analytics response**: previously returned a PNG image; now returns JSON by default (`/analytics/{code}`). PNG chart moved to `/analytics/{code}/chart`.
- **JWT tokens**: now include `jti` claim for proper per-token revocation.
- **Short code generation**: `random.choices` → `secrets.choice` (cryptographically secure).

### Security fixes (dependencies)

| Package | From | To | CVE / Advisory |
|---|---|---|---|
| `Pillow` | 10.3.0 | 12.2.0 | FITS GZIP decompression bomb; PSD out-of-bounds write |
| `python-jose` | 3.3.0 | 3.4.0 | ECDSA algorithm confusion with OpenSSH keys |
| `python-multipart` | 0.0.9 | 0.0.22 | Arbitrary file write; DoS via malformed form boundary |

---

## [1.0.0] — 2023 (original Flask implementation)

Initial release of Scissors API built with **Flask + Flask-RESTX**.

### Features
- URL shortening with optional custom short codes.
- Redirect with in-process SimpleCache (30 s TTL).
- Click tracking with GeoIP source via GeoIPify.
- QR code generation (PNG).
- Analytics as a PNG bar chart image.
- URL history per authenticated user.
- JWT authentication (Flask-JWT-Extended) with in-memory token blacklist.
- Flask-Limiter rate limiting.
- Flask-Migrate / Alembic database migrations.
- Flask-CORS.
- PostgreSQL in production, SQLite for development/test.

[2.0.0]: https://github.com/spartan124/scissors_api/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/spartan124/scissors_api/releases/tag/v1.0.0
