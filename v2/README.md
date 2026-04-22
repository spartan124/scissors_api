# Scissors API v2

A high-performance URL shortening service rebuilt from the ground up with **FastAPI**, async SQLAlchemy, and Redis caching. All routes are designed to execute in under 100 ms at scale.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick start (local)](#quick-start-local)
- [Docker (recommended)](#docker-recommended)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Database migrations](#database-migrations)
- [Deploying to Render](#deploying-to-render)
- [Running tests](#running-tests)

---

## Features

| Capability | Detail |
|---|---|
| URL shortening | Auto-generated or custom short codes (alphanumeric, 3–20 chars) |
| Redirect | Redis-cached hot path — resolves in ~0.5 ms, no DB query on cache hit |
| Click analytics | Background-task recording (non-blocking), JSON stats + PNG bar chart |
| QR codes | PNG QR code per short URL, Redis-cached |
| URL history | All links for the authenticated user |
| Authentication | JWT (access + refresh tokens), Redis-backed token blacklist on logout |
| Rate limiting | Per-IP via SlowAPI (configurable) |
| CORS | Configurable via `ALLOWED_ORIGINS` |
| GeoIP | Optional — skipped gracefully when `GEOIPIFY_API_KEY` is absent |

---

## Architecture

```
┌─────────────────────────────────────────┐
│              FastAPI app                │
│  uvicorn[standard]  ·  4 workers        │
│                                         │
│  /auth/*   JWT signup / login / logout  │
│  /shorten  create short URL             │
│  /{code}   redirect (Redis hot path)    │
│  /history  user's links                 │
│  /analytics/{code}  click stats         │
│  /{code}/qrcode  PNG QR code            │
└──────┬──────────────────────┬───────────┘
       │ asyncpg              │ aioredis
┌──────▼──────┐        ┌──────▼──────┐
│ PostgreSQL  │        │    Redis    │
│  (data)     │        │  (cache +   │
│             │        │  blacklist) │
└─────────────┘        └─────────────┘
```

- **Database**: async SQLAlchemy 2.0 + asyncpg, connection pool of 10+20
- **Cache**: Redis for redirect lookups (TTL 300 s), URL lookups (30 s), analytics + QR codes (60 s)
- **Click tracking**: `BackgroundTasks` — the 302 is sent before the DB write begins
- **Migrations**: Alembic with async engine

---

## Quick start (local)

### Prerequisites

- Python 3.12+
- PostgreSQL 15+ **or** leave `DATABASE_URL` as SQLite for development
- Redis 7+ **or** set `REDIS_URL` to a free cloud Redis (see [Deploying to Render](#deploying-to-render))

```bash
# 1. enter the v2 directory
cd v2

# 2. create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. install dependencies
pip install -r requirements.txt

# 4. copy and edit environment variables
cp .env.example .env
# edit .env — at minimum set SECRET_KEY, JWT_SECRET_KEY, DATABASE_URL, REDIS_URL

# 5. run database migrations
alembic upgrade head

# 6. start the dev server
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Docker (recommended)

### Start everything with one command

```bash
cd v2
cp .env.example .env    # edit values as needed
docker compose up --build
```

This starts:

| Service | Image | Port |
|---|---|---|
| `app` | built from `./Dockerfile` | `8000` |
| `postgres` | `postgres:16-alpine` | `5432` (internal) |
| `redis` | `redis:7-alpine` | `6379` (internal) |

The app container runs `alembic upgrade head` before starting uvicorn, so the schema is always up to date on boot.

### Useful commands

```bash
# view logs
docker compose logs -f app

# run tests inside the container
docker compose run --rm app python -m pytest tests/ -v

# stop everything and remove volumes
docker compose down -v
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in the values. All variables have safe defaults for local development (SQLite + localhost Redis), but **must** be set for production.

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `dev` | `dev` / `prod` |
| `SECRET_KEY` | `changeme` | App secret — **change in production** |
| `DEBUG` | `false` | Enable SQLAlchemy query logging |
| `DATABASE_URL` | SQLite | Full async DB URL — see examples below |
| `JWT_SECRET_KEY` | `changeme-jwt` | JWT signing key — **change in production** |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRES` | `120` hours | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRES` | `272` hours | Refresh token lifetime |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CACHE_TTL_REDIRECT` | `300` | Redirect cache TTL (seconds) |
| `CACHE_TTL_SHORT` | `30` | Short cache TTL (seconds) |
| `CACHE_TTL_LONG` | `60` | Medium cache TTL (seconds) |
| `RATE_LIMIT_DEFAULT` | `1000/day;50/hour` | SlowAPI default limits |
| `GEOIPIFY_API_KEY` | _(empty)_ | Optional GeoIPify key — skipped if absent |
| `ALLOWED_ORIGINS` | `["*"]` | JSON list of CORS origins |

**`DATABASE_URL` examples:**

```env
# PostgreSQL (production)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/scissors

# Docker Compose (uses service name as host)
DATABASE_URL=postgresql+asyncpg://scissors:scissors@postgres:5432/scissors

# SQLite (local dev / CI only)
DATABASE_URL=sqlite+aiosqlite:///./scissors_v2.db
```

---

## API reference

Interactive docs are always available at `/docs` (Swagger UI) and `/redoc`.

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | — | Register a new user |
| `POST` | `/auth/login` | — | Login, returns access + refresh tokens |
| `POST` | `/auth/refresh` | Refresh token | Issue a new access token |
| `POST` | `/auth/logout` | Bearer token | Blacklist the current token |
| `GET` | `/auth/user` | Bearer token | Get current user profile |

### URLs

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/shorten` | Bearer token | Shorten a URL (custom or auto code) |
| `GET` | `/{short_code}` | — | Redirect to original URL |
| `GET` | `/shortened/{short_code}` | Bearer token | Get full shortened URL string |
| `DELETE` | `/shortened/{short_code}` | Bearer token | Delete a short URL |
| `GET` | `/{short_code}/qrcode` | Bearer token | Download PNG QR code |
| `GET` | `/analytics/{short_code}` | Bearer token | JSON click analytics |
| `GET` | `/analytics/{short_code}/chart` | Bearer token | PNG bar chart of clicks by source |
| `GET` | `/history` | Bearer token | All URLs created by current user |
| `GET` | `/health` | — | Health check |

---

## Database migrations

Alembic is configured with the async engine. To generate a new migration after changing a model:

```bash
# inside v2/
alembic revision --autogenerate -m "describe your change"
alembic upgrade head

# roll back one step
alembic downgrade -1
```

---

## Deploying to Render

### Render free-tier compatibility

| Service | Free tier | Notes |
|---|---|---|
| **Web Service** (Docker) | ✅ Yes | Spins down after 15 min inactivity; first request is slower |
| **PostgreSQL** | ✅ Yes | 90-day expiry on free databases; upgrade for persistence |
| **Redis** | ❌ No | Redis requires a paid plan on Render ($10+/month) |

> **Redis on the free tier**: The app degrades gracefully — cache misses fall through to the database, so it still functions without Redis. For a free Redis instance use **[Upstash](https://upstash.com/)** (10 000 commands/day free) or **[Redis Cloud](https://redis.io/cloud/)** (30 MB free). Copy the `rediss://` URL into `REDIS_URL`.

### One-click deploy

A `render.yaml` is included. Push the repo to GitHub, connect it in the Render dashboard, and Render will detect the blueprint automatically.

```bash
# Set these secret environment variables in the Render dashboard:
SECRET_KEY=<generate with: openssl rand -hex 32>
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
DATABASE_URL=<render postgres internal URL or external URL>
REDIS_URL=<upstash or redis cloud URL>
```

### Manual deploy steps

1. Create a new **Web Service** → select your repo → choose **Docker** as environment.
2. Set the root directory to `v2`.
3. Set the start command (already in `render.yaml`): `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Add the environment variables from the table above.
5. Create a **PostgreSQL** database and copy the internal connection string to `DATABASE_URL`.
6. Add a Redis instance (paid) or an external free Redis URL.

---

## Running tests

```bash
cd v2
pip install -r requirements.txt pytest-asyncio
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database and mock Redis, so no external services are required.

```
tests/test_auth.py   — signup, login, refresh, logout, get user (9 tests)
tests/test_urls.py   — shorten, redirect, delete, history, analytics, QR (13 tests)
```
