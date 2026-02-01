.PHONY: help sync install test test-file test-unit test-integration test-property coverage lint format typecheck clean all check

# Default target
help:
	@echo "mcp-context-graph Development Commands"
	@echo "======================================="
	@echo ""
	@echo "Setup:"
	@echo "  make sync        - Sync dependencies (uv sync --dev)"
	@echo "  make install     - Alias for sync"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests with coverage"
	@echo "  make test-unit   - Run only unit tests"
	@echo "  make test-integration - Run only integration tests"
	@echo "  make test-property    - Run only property-based tests"
	@echo "  make test-file FILE=<path> - Run specific test file"
	@echo "                    Example: make test-file FILE=tests/unit/test_models.py"
	@echo "  make coverage    - Generate HTML coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Run ruff linter"
	@echo "  make format      - Format code with black and ruff"
	@echo "  make typecheck   - Run mypy type checker"
	@echo "  make check       - Run all checks (lint + typecheck + test)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Remove build artifacts and caches"
	@echo "  make all         - sync + check"

# Setup
sync:
	uv sync --dev

install: sync

# Testing
test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-property:
	uv run pytest tests/property/ -v

# Run specific test file: make test-file FILE=tests/unit/test_models.py
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=<path>"; \
		echo "Example: make test-file FILE=tests/unit/test_models.py"; \
		exit 1; \
	fi
	uv run pytest $(FILE) -v

# Generate HTML coverage report
coverage:
	uv run pytest --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Code Quality
lint:
	uv run ruff check src/ tests/

format:
	uv run ruff check --fix src/ tests/
	uv run black src/ tests/

typecheck:
	uv run mypy src/

# Run all checks
check: lint typecheck test

# Utilities
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Full workflow
all: sync check
