"""
Tailwind CSS connector - reads config file for version, plugins, and theme info.
"""

import json
import re
from pathlib import Path
from typing import Optional

from codrsync.connect.base import ConnectorBase, ConnectorResult


TAILWIND_CONFIGS = [
    "tailwind.config.js",
    "tailwind.config.ts",
    "tailwind.config.mjs",
    "tailwind.config.cjs",
]

# Common Tailwind plugins
KNOWN_PLUGINS = [
    "@tailwindcss/forms",
    "@tailwindcss/typography",
    "@tailwindcss/aspect-ratio",
    "@tailwindcss/container-queries",
    "tailwindcss-animate",
    "daisyui",
    "flowbite",
]


class TailwindConnector(ConnectorBase):
    def service_name(self) -> str:
        return "tailwind"

    def check(self, project_path: Path) -> ConnectorResult:
        # Find tailwind config file
        config_path = None
        for name in TAILWIND_CONFIGS:
            candidate = project_path / name
            if candidate.exists():
                config_path = candidate
                break

        if config_path is None:
            return ConnectorResult(
                service="tailwind",
                connected=False,
                status="not_configured",
            )

        details: dict = {"config_file": config_path.name}

        # Try to read version from package.json
        version = self._get_version(project_path)
        if version:
            details["version"] = version

        # Detect plugins from package.json
        plugins = self._get_plugins(project_path)
        if plugins:
            details["plugins"] = plugins

        # Try to read config content for theme info
        try:
            content = config_path.read_text(errors="replace")
            if "darkMode" in content:
                details["dark_mode"] = True
            if "theme:" in content or "theme :" in content or "theme:{" in content:
                details["custom_theme"] = True
        except OSError:
            pass

        return ConnectorResult(
            service="tailwind",
            connected=True,
            status="connected",
            details=details,
        )

    def _get_version(self, project_path: Path) -> Optional[str]:
        pkg_path = project_path / "package.json"
        if not pkg_path.exists():
            return None
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))
            version = all_deps.get("tailwindcss", "")
            # Strip semver prefixes
            return re.sub(r"^[\^~>=<]+", "", version) if version else None
        except (json.JSONDecodeError, OSError):
            return None

    def _get_plugins(self, project_path: Path) -> list[str]:
        pkg_path = project_path / "package.json"
        if not pkg_path.exists():
            return []
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))
            return [p for p in KNOWN_PLUGINS if p in all_deps]
        except (json.JSONDecodeError, OSError):
            return []
