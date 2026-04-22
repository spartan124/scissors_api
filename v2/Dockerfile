# ── Stage 1: build dependencies ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools needed for some wheels (e.g. cryptography, asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Runtime system dependency for asyncpg / psycopg2 (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create a non-root user
RUN groupadd --gid 1001 appgroup \
    && useradd  --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy application source
COPY --chown=appuser:appgroup . .

USER appuser

# Expose the port uvicorn listens on
EXPOSE 8000

# Run Alembic migrations then start the server.
# $PORT is provided by Render/Heroku; falls back to 8000 locally.
CMD alembic upgrade head \
    && uvicorn main:app \
       --host 0.0.0.0 \
       --port "${PORT:-8000}" \
       --workers "${WORKERS:-4}" \
       --proxy-headers \
       --forwarded-allow-ips "*"
