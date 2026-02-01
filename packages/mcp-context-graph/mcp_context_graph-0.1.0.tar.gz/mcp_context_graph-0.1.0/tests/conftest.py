"""Shared pytest fixtures for mcp-context-graph tests."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def python_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to Python test fixtures."""
    return fixtures_dir / "python"


@pytest.fixture
def typescript_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to TypeScript test fixtures."""
    return fixtures_dir / "typescript"


@pytest.fixture
def sample_python_file(python_fixtures_dir: Path) -> Path:
    """Return the path to the sample Python file."""
    return python_fixtures_dir / "sample.py"


@pytest.fixture
def sample_typescript_file(typescript_fixtures_dir: Path) -> Path:
    """Return the path to the sample TypeScript file."""
    return typescript_fixtures_dir / "sample.ts"


@pytest.fixture
def sample_javascript_file(typescript_fixtures_dir: Path) -> Path:
    """Return the path to the sample JavaScript file."""
    return typescript_fixtures_dir / "sample.js"
