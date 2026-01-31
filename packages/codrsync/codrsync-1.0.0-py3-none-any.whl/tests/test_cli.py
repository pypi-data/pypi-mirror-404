"""
Tests for the CLI commands.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from codrsync.cli import app
from codrsync import __version__


runner = CliRunner()


class TestVersionCommand:
    """Tests for --version flag."""

    def test_version_shows_version(self):
        """--version should show the version number."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_short_flag(self):
        """Short -v flag should also work."""
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestHelpCommand:
    """Tests for --help flag."""

    def test_help_shows_commands(self):
        """--help should list available commands."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Check that main commands are listed
        assert "status" in result.stdout.lower() or "Status" in result.stdout
        assert "init" in result.stdout.lower() or "Init" in result.stdout


class TestStatusCommand:
    """Tests for status command."""

    @patch("codrsync.local.status.run")
    def test_status_calls_run(self, mock_run):
        """status command should call status.run()."""
        mock_run.return_value = None

        result = runner.invoke(app, ["status"])

        # Should call the run function
        mock_run.assert_called_once()

    @patch("codrsync.local.status.run")
    def test_status_with_mini_flag(self, mock_run):
        """status --mini should pass mini=True."""
        mock_run.return_value = None

        result = runner.invoke(app, ["status", "--mini"])

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("mini") is True


class TestScanCommand:
    """Tests for scan command."""

    @patch("codrsync.scanner.scan.run")
    def test_scan_calls_run(self, mock_run):
        """scan command should call scan.run()."""
        mock_run.return_value = None

        result = runner.invoke(app, ["scan"])

        mock_run.assert_called_once()

    @patch("codrsync.scanner.scan.run")
    def test_scan_with_github_flag(self, mock_run):
        """scan --github should pass github=True."""
        mock_run.return_value = None

        result = runner.invoke(app, ["scan", "--github"])

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("github") is True

    @patch("codrsync.scanner.scan.run")
    def test_scan_with_docs_flag(self, mock_run):
        """scan --docs should pass docs=True."""
        mock_run.return_value = None

        result = runner.invoke(app, ["scan", "--docs"])

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("docs") is True


class TestConnectCommand:
    """Tests for connect command."""

    @patch("codrsync.connect.connect.run")
    def test_connect_calls_run(self, mock_run):
        """connect command should call connect.run()."""
        mock_run.return_value = None

        result = runner.invoke(app, ["connect"])

        mock_run.assert_called_once()

    @patch("codrsync.connect.connect.run")
    def test_connect_with_service(self, mock_run):
        """connect <service> should pass service name."""
        mock_run.return_value = None

        result = runner.invoke(app, ["connect", "supabase"])

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("service") == "supabase"


class TestDoctorCommand:
    """Tests for doctor command."""

    @patch("codrsync.utils.doctor.run_diagnostics")
    def test_doctor_calls_diagnostics(self, mock_diag):
        """doctor command should call run_diagnostics()."""
        mock_diag.return_value = None

        result = runner.invoke(app, ["doctor"])

        mock_diag.assert_called_once()
