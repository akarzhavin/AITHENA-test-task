FROM python:3.12-slim

# Environment variables configuration:
# PYTHONDONTWRITEBYTECODE - prevent python from writing .pyc files
# PYTHONUNBUFFERED - disable stdout/stderr buffering for real-time logs
# PYTHONPATH - ensure python finds the analyzer module
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup -s /sbin/nologin -d /app appuser

WORKDIR /app

# Upgrade pip and install dependencies as root
RUN pip install --upgrade pip --no-cache-dir

# Copy project manifest and source code
COPY pyproject.toml .
COPY src/ /app/src/

# Install the package and its dependencies (including dev tools for tests/linting)
RUN pip install --no-cache-dir ".[dev]"

# Create data and output directories with correct permissions for appuser
RUN mkdir -p /app/data /app/output && \
    chown -R appuser:appgroup /app

# Switch to the non-root user for execution
USER appuser

# Execute the analysis pipeline on container start
CMD ["python", "-m", "analyzer"]
