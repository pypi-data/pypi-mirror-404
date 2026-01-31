"""
Base classes for service connectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ConnectorResult:
    """Result from a connector check."""

    service: str
    connected: bool
    status: str  # "connected" | "not_configured" | "skipped" | "error"
    details: dict = field(default_factory=dict)
    cli_available: bool = False

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "connected": self.connected,
            "status": self.status,
            "details": self.details,
            "cli_available": self.cli_available,
        }


class ConnectorBase(ABC):
    """Abstract base class for service connectors."""

    @abstractmethod
    def service_name(self) -> str:
        """Return the service identifier (e.g. 'supabase')."""

    def required_cli(self) -> Optional[str]:
        """Return the CLI binary name required, or None."""
        return None

    @abstractmethod
    def check(self, project_path: Path) -> ConnectorResult:
        """Check the connection/configuration status for this service."""
