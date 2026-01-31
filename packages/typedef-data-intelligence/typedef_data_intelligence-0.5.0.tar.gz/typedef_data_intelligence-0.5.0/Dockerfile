# Production Dockerfile for FastAPI Backend
# Multi-stage build for optimized image size
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /workspace

# Copy workspace configuration
COPY pyproject.toml uv.lock ./
COPY typedef_data_intelligence/pyproject.toml ./typedef_data_intelligence/
COPY typedef_data_intelligence/README.pypi.md ./typedef_data_intelligence/

# Copy source code
COPY typedef_data_intelligence/src ./typedef_data_intelligence/src

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
  curl git build-essential

# Install dependencies with frozen lockfile (reproducible builds)
# Use FalkorDB backend for production
# --all-packages ensures workspace members are installed
RUN uv sync --frozen --package typedef-data-intelligence

# ============================================================================
# Runtime Stage
# ============================================================================
FROM python:3.12-slim

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy virtual environment from builder
COPY --from=builder /workspace/.venv /workspace/.venv

# Copy source code
COPY --from=builder /workspace/typedef_data_intelligence /workspace/typedef_data_intelligence

# Set environment
ENV PATH="/workspace/.venv/bin:$PATH"
ENV PYTHONPATH="/workspace/typedef_data_intelligence/src"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
  chown -R appuser:appuser /workspace

USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run backend server
# Config file should be mounted at runtime via volume
CMD ["python", "-m", "lineage.api.pydantic"]
