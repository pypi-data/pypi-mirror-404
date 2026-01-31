# =============================================================================
# Production Dockerfile for IdentityPlanKit Application
# =============================================================================
# Multi-stage build for optimal image size and security
#
# Build: docker build -t myapp:latest -f examples/prod/Dockerfile .
# Run:   docker run -p 8000:8000 --env-file .env.production myapp:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (production only, no dev dependencies)
RUN uv sync --frozen --no-dev --extra metrics

# -----------------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

# Security: Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY examples/prod/production_setup.py ./app.py

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Default to production environment
    IPK_ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Change to non-root user
USER appuser

# Run the application with uvicorn
# Note: Workers are handled by uvicorn, not gunicorn, for simplicity
# For higher performance, consider using gunicorn with uvicorn workers
CMD ["python", "-m", "uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]

# =============================================================================
# Alternative: Production with Gunicorn (higher performance)
# =============================================================================
# Uncomment below and comment the CMD above for gunicorn-based deployment
#
# RUN pip install gunicorn
# CMD ["gunicorn", "app:app", \
#      "-w", "4", \
#      "-k", "uvicorn.workers.UvicornWorker", \
#      "-b", "0.0.0.0:8000", \
#      "--access-logfile", "-", \
#      "--error-logfile", "-", \
#      "--capture-output", \
#      "--enable-stdio-inheritance"]
