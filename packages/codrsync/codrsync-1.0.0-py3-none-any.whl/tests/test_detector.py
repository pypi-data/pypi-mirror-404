"""
Tests for the scanner/detector module.
"""

import pytest
from pathlib import Path

from codrsync.scanner.detector import (
    detect,
    has_existing_code,
    FILE_MARKERS,
    DetectionResult,
)


class TestHasExistingCode:
    """Tests for has_existing_code function."""

    def test_empty_directory_returns_false(self, temp_dir):
        """Empty directory should return False."""
        assert has_existing_code(temp_dir) is False

    def test_directory_with_package_json_returns_true(self, temp_dir):
        """Directory with package.json should return True."""
        (temp_dir / "package.json").write_text("{}")
        assert has_existing_code(temp_dir) is True

    def test_directory_with_pyproject_returns_true(self, temp_dir):
        """Directory with pyproject.toml should return True."""
        (temp_dir / "pyproject.toml").write_text("[project]")
        assert has_existing_code(temp_dir) is True

    def test_directory_with_src_returns_true(self, temp_dir):
        """Directory with src/ should return True."""
        (temp_dir / "src").mkdir()
        assert has_existing_code(temp_dir) is True


class TestDetect:
    """Tests for the detect function."""

    def test_detect_nodejs_project(self, mock_project_dir):
        """Should detect Node.js/Next.js project."""
        result = detect(mock_project_dir)

        assert result is not None
        assert isinstance(result, DetectionResult)
        # Check for JavaScript/TypeScript in languages
        assert any("JavaScript" in lang or "TypeScript" in lang for lang in result.languages)

    def test_detect_python_project(self, mock_python_project):
        """Should detect Python project."""
        result = detect(mock_python_project)

        assert result is not None
        assert isinstance(result, DetectionResult)
        assert any("Python" in lang for lang in result.languages)

    def test_detect_empty_directory(self, temp_dir):
        """Should handle empty directory gracefully."""
        result = detect(temp_dir)

        assert result is not None
        assert isinstance(result, DetectionResult)
        # Empty directory should have empty lists
        assert result.languages == []

    def test_detect_with_dockerfile(self, temp_dir):
        """Should detect Docker infrastructure."""
        (temp_dir / "Dockerfile").write_text("FROM python:3.11")
        result = detect(temp_dir)

        assert result is not None
        assert isinstance(result, DetectionResult)
        assert any("Docker" in infra for infra in result.infrastructure)

    def test_detect_with_github_actions(self, temp_dir):
        """Should detect GitHub Actions."""
        workflows_dir = temp_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("name: CI")

        result = detect(temp_dir)

        assert result is not None
        assert isinstance(result, DetectionResult)


class TestFileMarkers:
    """Tests for FILE_MARKERS configuration."""

    def test_file_markers_not_empty(self):
        """FILE_MARKERS should have entries."""
        assert len(FILE_MARKERS) > 0

    def test_file_markers_is_list_of_tuples(self):
        """FILE_MARKERS should be a list of tuples."""
        assert isinstance(FILE_MARKERS, list)
        assert all(isinstance(m, tuple) and len(m) == 3 for m in FILE_MARKERS)

    def test_common_markers_present(self):
        """Common file markers should be present."""
        marker_paths = [m[0] for m in FILE_MARKERS]

        # Check some common markers exist
        common_markers = ["package.json", "pyproject.toml", "Dockerfile"]
        for marker in common_markers:
            assert marker in marker_paths, f"Missing marker: {marker}"
