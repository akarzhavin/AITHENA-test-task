.PHONY: setup install test run docker-run clean lint format

# Variables
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest
RUFF = $(VENV)/bin/ruff
MYPY = $(VENV)/bin/mypy

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup       - Create virtual environment and install dependencies"
	@echo "  make test        - Run automated tests (via pytest)"
	@echo "  make run         - Run analysis locally"
	@echo "  make lint        - Check code with linters (ruff, mypy)"
	@echo "  make format      - Format code (ruff)"
	@echo "  make docker-run  - Run analysis in Docker via docker-compose"
	@echo "  make clean       - Clear temporary files and output directory"

# Create virtual environment and install packages
setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "✅ Environment configured. To activate, run: source .venv/bin/activate"

# Run tests locally
test:
	$(PYTEST) -v

# Linting and formatting
lint:
	$(RUFF) check .
	$(MYPY) .

format:
	$(RUFF) format .
	$(RUFF) check --fix .

# Run analyzer locally
run:
	$(PYTHON) -m analyzer

# Run in Docker
docker-run:
	docker-compose up --build

# Clear caches and old results
clean:
	rm -rf output/*
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf *.egg-info/
	@echo "✅ Temporary files removed"
