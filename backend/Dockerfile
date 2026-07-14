# =============================================================================
# Prabhu AI Studio — Backend Dockerfile
# =============================================================================
#
# Multi-stage build:
#   builder  — installs dependencies in an isolated layer
#   final    — copies only the installed packages and application code
#
# Security:
#   - Runs as non-root user 'appuser' (uid 1000)
#   - No build tools (gcc, make, etc.) in the final image
#   - HEALTHCHECK instructs Docker when the container is considered healthy
#
# Layer caching:
#   - requirements.txt is copied and installed BEFORE the application code.
#     This ensures the expensive pip install step is cached as long as
#     requirements.txt hasn't changed, even if source code changes.
#
# Build args:
#   PYTHON_VERSION  Python version tag (default: 3.12-slim)
#   APP_ENV         "development" | "production" (controls dev deps install)
# =============================================================================

ARG PYTHON_VERSION=3.12-slim

# -----------------------------------------------------------------------------
# Stage 1: builder
# Installs all Python dependencies into a virtual environment.
# Using a venv makes it trivial to copy only the installed packages to final.
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS builder

WORKDIR /build

# System packages needed only to compile certain Python packages (e.g. asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment to isolate dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements first (cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Conditionally install dev requirements
ARG APP_ENV=production
COPY requirements-dev.txt .
RUN if [ "$APP_ENV" = "development" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
    fi

# -----------------------------------------------------------------------------
# Stage 2: final
# Minimal runtime image — no build tools, no cache, non-root user.
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS final

# Runtime system packages (curl for HEALTHCHECK, libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY --chown=appuser:appgroup . .

# Create the media directory and grant ownership to appuser
RUN mkdir -p /app/media && chown -R appuser:appgroup /app/media

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# ------------------------------------------------------------------
# HEALTHCHECK
# Docker will call this command every 30s.
# If it fails 3 consecutive times, the container is marked unhealthy.
# The /api/v1/health endpoint returns 200 when the app is ready.
# ------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ------------------------------------------------------------------
# Environment defaults (overridden by docker-compose or runtime env)
# ------------------------------------------------------------------
ENV APP_ENV=production \
    APP_DEBUG=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

# ------------------------------------------------------------------
# Default command
# Uses 1 worker per CPU core (Gunicorn + uvicorn workers).
# For development, docker-compose.override.yml overrides this to:
#   uvicorn app.main:app --reload
# ------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--http", "h11", \
     "--access-log", \
     "--no-use-colors"]
