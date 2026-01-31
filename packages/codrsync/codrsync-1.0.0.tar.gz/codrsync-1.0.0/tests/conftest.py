"""
Pytest configuration and fixtures for codrsync CLI tests.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_project_dir(temp_dir):
    """Create a mock project directory with common files."""
    # Create package.json (Node.js project)
    package_json = temp_dir / "package.json"
    package_json.write_text('{"name": "test-project", "version": "1.0.0", "dependencies": {"next": "14.0.0"}}')

    # Create src directory
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    # Create a sample file
    (src_dir / "index.ts").write_text("export const hello = 'world';")

    return temp_dir


@pytest.fixture
def mock_python_project(temp_dir):
    """Create a mock Python project directory."""
    # Create pyproject.toml
    pyproject = temp_dir / "pyproject.toml"
    pyproject.write_text('''
[project]
name = "test-project"
version = "1.0.0"
dependencies = ["fastapi>=0.100.0"]
''')

    # Create src directory
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    return temp_dir


@pytest.fixture
def mock_codrsync_dir(temp_dir):
    """Create a mock .codrsync directory structure."""
    codrsync_dir = temp_dir / ".codrsync"
    codrsync_dir.mkdir()

    # Create manifest.json
    manifest = codrsync_dir / "manifest.json"
    manifest.write_text('{"project": {"name": "test", "type": "webapp"}}')

    # Create progress.json
    progress = codrsync_dir / "progress.json"
    progress.write_text('{"phase": "building", "stories": []}')

    return temp_dir


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("CODRSYNC_HOME", "/tmp/codrsync-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture
def mock_ai_backend():
    """Create a mock AI backend."""
    backend = MagicMock()
    backend.generate.return_value = "Mock AI response"
    return backend
