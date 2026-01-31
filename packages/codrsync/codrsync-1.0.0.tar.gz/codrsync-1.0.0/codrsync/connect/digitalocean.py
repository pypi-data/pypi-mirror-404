"""
DigitalOcean connector - stub that detects doctl CLI availability.
"""

import shutil
from pathlib import Path

from codrsync.connect.base import ConnectorBase, ConnectorResult


class DigitalOceanConnector(ConnectorBase):
    def service_name(self) -> str:
        return "digitalocean"

    def required_cli(self) -> str | None:
        return "doctl"

    def check(self, project_path: Path) -> ConnectorResult:
        cli_available = shutil.which("doctl") is not None
        details: dict = {}

        # Check for DO App Platform config
        app_yaml = project_path / ".do" / "app.yaml"
        if app_yaml.exists():
            details["app_platform"] = True

        if cli_available:
            return ConnectorResult(
                service="digitalocean",
                connected=False,
                status="skipped",
                details={"note": "doctl detected, full integration not yet implemented"},
                cli_available=True,
            )

        return ConnectorResult(
            service="digitalocean",
            connected=False,
            status="skipped",
            details=details,
            cli_available=False,
        )
