"""
Vercel connector - check vercel CLI and project configuration.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from codrsync.connect.base import ConnectorBase, ConnectorResult


class VercelConnector(ConnectorBase):
    def service_name(self) -> str:
        return "vercel"

    def required_cli(self) -> Optional[str]:
        return "vercel"

    def check(self, project_path: Path) -> ConnectorResult:
        cli_available = shutil.which("vercel") is not None
        details: dict = {}

        # Check for vercel.json config
        vercel_json = project_path / "vercel.json"
        if vercel_json.exists():
            try:
                with open(vercel_json) as f:
                    config = json.load(f)
                details["config_file"] = True
                if "projectSettings" in config:
                    details["framework"] = config["projectSettings"].get("framework", "")
            except (json.JSONDecodeError, OSError):
                details["config_file"] = True

        # Check for .vercel directory (linked project)
        vercel_dir = project_path / ".vercel"
        if vercel_dir.is_dir():
            project_json = vercel_dir / "project.json"
            if project_json.exists():
                try:
                    with open(project_json) as f:
                        proj = json.load(f)
                    details["project_id"] = proj.get("projectId", "")
                    details["org_id"] = proj.get("orgId", "")
                except (json.JSONDecodeError, OSError):
                    pass

        # Try to get project name from CLI
        if cli_available:
            name = self._get_project_name(project_path)
            if name:
                details["project_name"] = name

        connected = bool(details.get("project_id") or details.get("config_file"))

        return ConnectorResult(
            service="vercel",
            connected=connected,
            status="connected" if connected else "not_configured",
            details=details,
            cli_available=cli_available,
        )

    def _get_project_name(self, project_path: Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["vercel", "project", "ls", "--json"],
                capture_output=True, text=True,
                cwd=str(project_path), timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, list) and data:
                        return data[0].get("name")
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None
