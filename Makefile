.PHONY: setup test test-live run run-rewrite docker-run clean lint format

# Variables
COMPOSE = docker-compose
RUN_CMD = $(COMPOSE) run --rm analyzer

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup       - Build docker image and prepare environment"
	@echo "  make test        - Run automated tests in Docker (excluding live)"
	@echo "  make test-live   - Run live acceptance tests in Docker"
	@echo "  make run         - Run analysis in Docker"
	@echo "  make run-rewrite - Run analysis in Docker with force rewrite"
	@echo "  make lint        - Check code with linters in Docker"
	@echo "  make format      - Format code in Docker"
	@echo "  make docker-run  - Same as 'make run'"
	@echo "  make clean       - Clear temporary files and output directory"

# Build docker image
setup:
	$(COMPOSE) build
	@echo "✅ Docker image built and ready."

# Run tests in Docker
test: setup
	$(RUN_CMD) pytest -v -m "not live"

test-live: setup
	$(RUN_CMD) pytest -v -m "live"

# Linting and formatting in Docker
lint: setup
	$(RUN_CMD) ruff check .
	$(RUN_CMD) mypy .

format: setup
	$(RUN_CMD) ruff format .
	$(RUN_CMD) ruff check --fix .

# Run analyzer in Docker
run: setup
	$(RUN_CMD) python -m analyzer

run-rewrite: setup
	$(RUN_CMD) /bin/sh -c "FORCE_REWRITE=True python -m analyzer"

# Run in Docker
docker-run: run

# Clear caches and old results
clean:
	rm -rf output/*
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf *.egg-info/
	@echo "✅ Temporary files removed"
