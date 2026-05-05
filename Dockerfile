FROM python:3.12-slim

# Environment variables configuration:
# PYTHONDONTWRITEBYTECODE - prevent python from writing .pyc files
# PYTHONUNBUFFERED - disable stdout/stderr buffering for real-time logs
# PYTHONPATH - ensure python finds the analyzer module
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip --no-cache-dir

# Copy project manifest and source code
COPY pyproject.toml .
COPY src/ /app/src/

# Install the package and its dependencies
RUN pip install --no-cache-dir .

# Execute the analysis pipeline on container start
CMD ["python", "-m", "analyzer"]
