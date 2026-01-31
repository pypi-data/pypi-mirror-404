"""
Connect orchestrator - runs all connectors and displays results.
"""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from codrsync.i18n import t
from codrsync.connect.base import ConnectorResult
from codrsync.connect.supabase import SupabaseConnector
from codrsync.connect.vercel import VercelConnector
from codrsync.connect.digitalocean import DigitalOceanConnector
from codrsync.connect.mcp import MCPConnector
from codrsync.connect.github import GitHubConnector
from codrsync.connect.tailwind import TailwindConnector

console = Console()

CONNECTORS: dict[str, type] = {
    "supabase": SupabaseConnector,
    "vercel": VercelConnector,
    "digitalocean": DigitalOceanConnector,
    "mcp": MCPConnector,
    "github": GitHubConnector,
    "tailwind": TailwindConnector,
}


def run(
    service: Optional[str] = None,
    path: Optional[Path] = None,
) -> list[ConnectorResult]:
    """Run connector checks and display results.

    If service is specified, only that connector is checked.
    Otherwise, all connectors are checked.
    """
    path = path or Path.cwd()
    console.print(f"\n{t('connect.checking')}\n")

    if service:
        if service not in CONNECTORS:
            available = ", ".join(CONNECTORS.keys())
            console.print(f"{t('common.error')} {t('connect.unknown_service', service=service, available=available)}")
            return []
        connectors_to_run = {service: CONNECTORS[service]}
    else:
        connectors_to_run = CONNECTORS

    results: list[ConnectorResult] = []
    for name, cls in connectors_to_run.items():
        connector = cls()
        result = connector.check(path)
        results.append(result)

    _render_results(results)

    # Save integrations.json
    output_dir = path / "doc" / "project"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "integrations.json"
    with open(output_path, "w") as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    console.print(f"{t('common.success')} {t('connect.result_saved', path=str(output_path))}\n")

    return results


def _render_results(results: list[ConnectorResult]):
    """Render connector results as a table."""
    table = Table(title=t("connect.header"), show_header=True, border_style="cyan")
    table.add_column(t("connect.service_col"), style="bold")
    table.add_column(t("connect.status_col"))
    table.add_column(t("connect.details_col"))
    table.add_column(t("connect.cli_col"))

    status_map = {
        "connected": t("connect.connected"),
        "not_configured": t("connect.not_configured"),
        "skipped": t("connect.skipped"),
        "error": t("connect.error"),
    }

    counts = {"connected": 0, "not_configured": 0, "skipped": 0, "error": 0}

    for r in results:
        status_text = status_map.get(r.status, r.status)
        detail_text = _format_details(r)

        if r.service in ("mcp",):
            cli_text = t("connect.cli_na")
        elif r.cli_available:
            cli_text = t("connect.cli_available")
        else:
            cli_text = t("connect.cli_missing")

        table.add_row(r.service, status_text, detail_text, cli_text)
        counts[r.status] = counts.get(r.status, 0) + 1

    console.print(table)
    console.print(f"\n{t('connect.summary', connected=counts['connected'], not_configured=counts['not_configured'], skipped=counts['skipped'])}")


def _format_details(r: ConnectorResult) -> str:
    """Format connector details for display."""
    d = r.details

    if r.service == "supabase":
        if d.get("url"):
            return t("connect.supabase_url", url=d["url"][:40])
        return t("connect.supabase_key_missing") if not d.get("anon_key_set") else ""

    if r.service == "vercel":
        if d.get("project_name"):
            return t("connect.vercel_project", name=d["project_name"])
        if d.get("project_id"):
            return t("connect.vercel_project", name=d["project_id"][:20])
        return t("connect.vercel_no_project")

    if r.service == "github":
        parts = []
        if d.get("user"):
            parts.append(t("connect.github_user", user=d["user"]))
        if d.get("repo"):
            parts.append(t("connect.github_repo", repo=d["repo"]))
        if d.get("reason"):
            return d["reason"]
        return " | ".join(parts) if parts else ""

    if r.service == "tailwind":
        parts = []
        if d.get("version"):
            parts.append(t("connect.tailwind_version", version=d["version"]))
        if d.get("plugins"):
            parts.append(t("connect.tailwind_plugins", plugins=", ".join(d["plugins"])))
        if d.get("config_file"):
            parts.append(d["config_file"])
        return " | ".join(parts) if parts else t("connect.tailwind_no_config")

    if r.service == "mcp":
        servers = d.get("servers", [])
        if servers:
            return t("connect.mcp_server_list", servers=", ".join(servers))
        return t("connect.mcp_none")

    if r.service == "digitalocean":
        if r.cli_available:
            return t("connect.digitalocean_detected")
        return t("connect.digitalocean_not_detected")

    return str(d) if d else ""
