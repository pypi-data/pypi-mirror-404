"""
GitHub connector - check gh CLI auth and repo info.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from codrsync.connect.base import ConnectorBase, ConnectorResult


class GitHubConnector(ConnectorBase):
    def service_name(self) -> str:
        return "github"

    def required_cli(self) -> Optional[str]:
        return "gh"

    def check(self, project_path: Path) -> ConnectorResult:
        cli_available = shutil.which("gh") is not None
        details: dict = {}

        if not cli_available:
            return ConnectorResult(
                service="github",
                connected=False,
                status="not_configured",
                details={"reason": "gh CLI not installed"},
                cli_available=False,
            )

        # Check auth status
        user = self._get_auth_user()
        if user:
            details["user"] = user
        else:
            return ConnectorResult(
                service="github",
                connected=False,
                status="not_configured",
                details={"reason": "not authenticated"},
                cli_available=True,
            )

        # Check repo
        repo = self._get_repo_name(project_path)
        if repo:
            details["repo"] = repo

        return ConnectorResult(
            service="github",
            connected=True,
            status="connected",
            details=details,
            cli_available=True,
        )

    def _get_auth_user(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["gh", "auth", "status", "--hostname", "github.com"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                # Extract username from output
                for line in result.stdout.splitlines() + result.stderr.splitlines():
                    if "Logged in to" in line and "account" in line:
                        # Format: "Logged in to github.com account USERNAME ..."
                        parts = line.split("account")
                        if len(parts) > 1:
                            return parts[1].strip().split()[0].strip("()")
                    if "as" in line.lower():
                        parts = line.split("as")
                        if len(parts) > 1:
                            return parts[-1].strip().split()[0].strip("()")
                return "authenticated"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    def _get_repo_name(self, project_path: Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                capture_output=True, text=True, cwd=str(project_path), timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None
