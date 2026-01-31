"""
Supabase connector - checks env vars, config, and optional CLI.
"""

import os
import shutil
from pathlib import Path

from codrsync.connect.base import ConnectorBase, ConnectorResult


class SupabaseConnector(ConnectorBase):
    def service_name(self) -> str:
        return "supabase"

    def required_cli(self) -> str | None:
        return "supabase"

    def check(self, project_path: Path) -> ConnectorResult:
        cli_available = shutil.which("supabase") is not None
        details: dict = {}

        # Check env vars
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        # Check .env files for keys
        if not supabase_url:
            supabase_url = self._read_env_var(project_path, "SUPABASE_URL") or \
                           self._read_env_var(project_path, "NEXT_PUBLIC_SUPABASE_URL")

        if not supabase_key:
            supabase_key = self._read_env_var(project_path, "SUPABASE_ANON_KEY") or \
                           self._read_env_var(project_path, "NEXT_PUBLIC_SUPABASE_ANON_KEY")

        if supabase_url:
            details["url"] = supabase_url
        if supabase_key:
            details["anon_key_set"] = True
        if supabase_service_key:
            details["service_key_set"] = True

        # Check for supabase config
        config_path = project_path / "supabase" / "config.toml"
        if config_path.exists():
            details["local_config"] = True

        connected = bool(supabase_url and supabase_key)

        return ConnectorResult(
            service="supabase",
            connected=connected,
            status="connected" if connected else "not_configured",
            details=details,
            cli_available=cli_available,
        )

    def _read_env_var(self, project_path: Path, var_name: str) -> str | None:
        """Try to read a variable from .env or .env.local files."""
        for env_file in [".env", ".env.local", ".env.development.local"]:
            env_path = project_path / env_file
            if not env_path.exists():
                continue
            try:
                for line in env_path.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    if key.strip() == var_name:
                        return value.strip().strip('"').strip("'")
            except OSError:
                continue
        return None
