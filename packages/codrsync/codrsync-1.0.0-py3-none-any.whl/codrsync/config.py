"""
Configuration management for codrsync CLI
"""

import os
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel


# Config file locations
CODRSYNC_HOME = Path.home() / ".codrsync"
CODRSYNC_CONFIG = CODRSYNC_HOME / "config.json"

# Legacy path for migration
_HITIT_HOME = Path.home() / ".hitit"


def migrate_from_hitit():
    """Migrate config from ~/.hitit to ~/.codrsync if needed.

    Copies files from the old directory to the new one.
    The old directory is kept as a backup (not deleted).
    """
    if not _HITIT_HOME.exists():
        return

    if CODRSYNC_HOME.exists():
        return

    CODRSYNC_HOME.mkdir(exist_ok=True)

    for src_file in _HITIT_HOME.iterdir():
        if src_file.is_file():
            shutil.copy2(src_file, CODRSYNC_HOME / src_file.name)

    # Leave a marker so the user knows migration happened
    marker = _HITIT_HOME / ".migrated_to_codrsync"
    marker.write_text("Migrated to ~/.codrsync on first run of codrsync.\n")


# Run migration on import
migrate_from_hitit()


class Config(BaseModel):
    """Global codrsync configuration"""

    # AI Backend
    ai_backend: str = "auto"  # auto, claude-code, anthropic-api, offline
    anthropic_api_key: Optional[str] = None

    # Language
    language: str = "en"

    # Preferences
    default_sprint_duration: int = 2  # weeks
    auto_research: bool = True
    explanation_level: str = "balanced"  # concise, balanced, detailed

    # Paths
    exports_dir: str = "exports"
    prps_dir: str = "PRPs"

    @classmethod
    def load(cls) -> "Config":
        """Load config from file or create default"""
        if CODRSYNC_CONFIG.exists():
            with open(CODRSYNC_CONFIG) as f:
                data = json.load(f)
            return cls(**data)
        return cls()

    def save(self):
        """Save config to file"""
        CODRSYNC_HOME.mkdir(exist_ok=True)
        with open(CODRSYNC_CONFIG, "w") as f:
            json.dump(self.model_dump(), f, indent=2)


@dataclass
class ProjectContext:
    """Context for current project"""

    root: Path
    manifest_path: Path
    progress_path: Path
    integrations_path: Path = None  # type: ignore[assignment]
    manifest: dict = field(default_factory=dict)
    progress: dict = field(default_factory=dict)
    integrations: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.integrations_path is None:
            self.integrations_path = self.root / "doc" / "project" / "integrations.json"

    @classmethod
    def load(cls, root: Optional[Path] = None) -> Optional["ProjectContext"]:
        """Load project context from current directory"""
        root = root or Path.cwd()

        manifest_path = root / "doc" / "project" / "manifest.json"
        progress_path = root / "doc" / "project" / "progress.json"
        integrations_path = root / "doc" / "project" / "integrations.json"

        if not manifest_path.exists():
            return None

        ctx = cls(
            root=root,
            manifest_path=manifest_path,
            progress_path=progress_path,
            integrations_path=integrations_path,
        )

        with open(manifest_path) as f:
            ctx.manifest = json.load(f)

        if progress_path.exists():
            with open(progress_path) as f:
                ctx.progress = json.load(f)

        if integrations_path.exists():
            with open(integrations_path) as f:
                ctx.integrations = json.load(f)

        return ctx

    def save(self):
        """Save manifest, progress, and integrations"""
        with open(self.manifest_path, "w") as f:
            json.dump(self.manifest, f, indent=2)

        with open(self.progress_path, "w") as f:
            json.dump(self.progress, f, indent=2)

        if self.integrations:
            with open(self.integrations_path, "w") as f:
                json.dump(self.integrations, f, indent=2)

    @property
    def project_name(self) -> str:
        return self.manifest.get("project", {}).get("name", "Unknown")

    @property
    def phase(self) -> str:
        return self.manifest.get("project", {}).get("phase", "unknown")

    @property
    def overall_progress(self) -> int:
        return self.progress.get("overall_progress", 0)


def get_config() -> Config:
    """Get global config"""
    return Config.load()


def get_project_context() -> Optional[ProjectContext]:
    """Get current project context"""
    return ProjectContext.load()


def require_project_context() -> ProjectContext:
    """Get project context or exit with error"""
    ctx = get_project_context()
    if ctx is None:
        from rich.console import Console
        from codrsync.i18n import t
        console = Console()
        console.print(f"{t('common.error')} {t('common.no_project')}")
        raise SystemExit(1)
    return ctx


def is_first_run() -> bool:
    """Check if this is the first time codrsync is run (no config file)."""
    return not CODRSYNC_CONFIG.exists()
