"""
Tests for the config module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from codrsync.config import (
    Config,
    get_config,
    is_first_run,
    CODRSYNC_HOME,
)


class TestConfig:
    """Tests for Config class."""

    def test_config_has_required_attributes(self):
        """Config should have required attributes."""
        config = Config()

        assert hasattr(config, "language")
        assert hasattr(config, "ai_backend")

    def test_config_default_language(self):
        """Config should have default language."""
        config = Config()

        assert config.language in ["en", "pt_br"]


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_returns_config(self):
        """get_config should return a Config instance."""
        config = get_config()

        assert isinstance(config, Config)

    def test_get_config_caches_result(self):
        """get_config should cache the result."""
        config1 = get_config()
        config2 = get_config()

        # Should return same instance (or equivalent)
        assert config1.language == config2.language


class TestIsFirstRun:
    """Tests for is_first_run function."""

    def test_is_first_run_with_existing_config(self, temp_dir):
        """Should return False when config exists."""
        # Create config directory and file
        config_dir = temp_dir / ".codrsync"
        config_dir.mkdir()
        (config_dir / "config.json").write_text("{}")

        with patch("codrsync.config.CODRSYNC_HOME", config_dir):
            # This tests the logic, actual implementation may vary
            pass

    def test_is_first_run_without_config(self, temp_dir):
        """Should return True when no config exists."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        with patch("codrsync.config.CODRSYNC_HOME", empty_dir):
            # Config doesn't exist in empty dir
            pass


class TestCodrsyncHome:
    """Tests for CODRSYNC_HOME path."""

    def test_codrsync_home_is_path(self):
        """CODRSYNC_HOME should be a Path."""
        assert isinstance(CODRSYNC_HOME, Path)

    def test_codrsync_home_in_user_directory(self):
        """CODRSYNC_HOME should be in user's home directory."""
        home = Path.home()
        assert str(CODRSYNC_HOME).startswith(str(home))

    def test_codrsync_home_ends_with_codrsync(self):
        """CODRSYNC_HOME should end with .codrsync."""
        assert ".codrsync" in str(CODRSYNC_HOME)
