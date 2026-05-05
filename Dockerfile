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

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.4.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy project manifest
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies
RUN poetry install --no-root --with dev

# Copy source code
COPY src/ /app/src/

# Install the project itself
RUN poetry install --with dev

# Create data and output directories with correct permissions for appuser
RUN mkdir -p /app/data /app/output && \
    chown -R appuser:appgroup /app

# Switch to the non-root user for execution
USER appuser

# Execute the analysis pipeline on container start
CMD ["python", "-m", "analyzer"]
