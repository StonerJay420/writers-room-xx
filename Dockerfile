# Multi-stage build for Writers Room X
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash wrx

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY api/pyproject.toml api/uv.lock ./
RUN pip install uv && \
    uv venv /app/venv && \
    . /app/venv/bin/activate && \
    uv pip install -r pyproject.toml

# Copy application code
COPY api/ ./api/
COPY frontend/dist/ ./frontend/dist/

# Create necessary directories
RUN mkdir -p /app/data/manuscript /app/data/codex /app/logs && \
    chown -R wrx:wrx /app

# Switch to app user
USER wrx

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["/app/venv/bin/python", "-m", "uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]