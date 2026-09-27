# ==============================================================================
# Production Dockerfile for Employee Management System (StaffPulse)
# Hardened, non-root user, optimized layer caching, and native HEALTHCHECK.
# ==============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable immediate log flushes
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies if required for binary builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies in isolated layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and frontend static assets
COPY app ./app
COPY static ./static

# Create non-privileged system user for container security
RUN useradd --create-home --uid 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Docker-level healthcheck validating HTTP liveness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
