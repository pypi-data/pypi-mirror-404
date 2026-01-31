"""
Scan orchestrator - wires detector, doc_scanner, github_scanner, and context_generator.
"""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codrsync.i18n import t
from codrsync.scanner.detector import detect
from codrsync.scanner.doc_scanner import scan_docs
from codrsync.scanner.github_scanner import scan_github
from codrsync.scanner.context_generator import generate_context

console = Console()


def run(
    path: Optional[Path] = None,
    github: bool = False,
    docs: bool = False,
    deep: bool = False,
    backend=None,
) -> dict:
    """Run the project scan.

    Returns a dict with all scan results.
    """
    path = path or Path.cwd()
    console.print(f"\n{t('scan.scanning', path=str(path))}\n")

    # 1. Always: detect stack
    detection = detect(path)

    _render_detection(detection)

    scan_result: dict = {
        "path": str(path),
        "detection": detection.to_dict(),
    }

    # 2. Optional: scan docs
    doc_result = None
    if docs:
        doc_result = scan_docs(path)
        _render_docs(doc_result)
        scan_result["docs"] = doc_result.to_dict()

    # 3. Optional: scan GitHub
    gh_result = None
    if github:
        gh_result = scan_github(path)
        _render_github(gh_result)
        scan_result["github"] = gh_result.to_dict()

    # 4. Optional: deep analysis
    if deep and backend is not None:
        console.print(f"\n[bold]{t('scan.deep_header')}[/bold]")
        console.print(f"  {t('scan.deep_generating')}")
        saved = generate_context(path, detection, doc_result, gh_result, backend=backend)
        if saved:
            console.print(f"  {t('common.success')} {t('scan.deep_saved', path=saved)}")
            scan_result["context_path"] = saved
        else:
            console.print(f"  {t('scan.deep_failed', error='AI backend unavailable or failed')}")

    # Summary
    console.print(f"\n{t('scan.summary', languages=len(detection.languages), frameworks=len(detection.frameworks), databases=len(detection.databases))}")

    # Save result
    output_dir = path / "doc" / "project"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "scan-result.json"
    with open(output_path, "w") as f:
        json.dump(scan_result, f, indent=2)
    console.print(f"{t('common.success')} {t('scan.result_saved', path=str(output_path))}\n")

    return scan_result


def _render_detection(detection):
    """Render detection results to console."""
    if detection.is_empty:
        console.print(f"  {t('scan.no_detections')}")
        return

    table = Table(title=t("scan.header"), show_header=True, border_style="cyan")
    table.add_column("Category", style="bold")
    table.add_column("Detected")

    categories = [
        (t("scan.languages_header"), detection.languages),
        (t("scan.frameworks_header"), detection.frameworks),
        (t("scan.databases_header"), detection.databases),
        (t("scan.infrastructure_header"), detection.infrastructure),
        (t("scan.tools_header"), detection.tools),
    ]

    for label, items in categories:
        if items:
            table.add_row(label, ", ".join(items))

    console.print(table)

    if detection.package_json:
        deps = detection.package_json.get("dependencies", {})
        dev_deps = detection.package_json.get("devDependencies", {})
        total = len(deps) + len(dev_deps)
        console.print(f"  {t('scan.package_json_deps', count=total)}")

    if detection.pyproject:
        name = detection.pyproject.get("project", {}).get("name", "")
        if name:
            console.print(f"  {t('scan.pyproject_name', name=name)}")


def _render_docs(doc_result):
    """Render documentation scan results."""
    console.print(f"\n[bold]{t('scan.docs_header')}[/bold]")
    if not doc_result.found_files:
        console.print(f"  {t('scan.docs_none')}")
        return

    console.print(f"  {t('scan.docs_found', files=', '.join(doc_result.found_files))}")

    if doc_result.readme_content:
        lines = doc_result.readme_content.split("\n")
        preview = "\n".join(lines[:10])
        console.print(Panel(
            preview,
            title=t("scan.readme_preview", lines=len(lines)),
            border_style="dim",
        ))


def _render_github(gh_result):
    """Render GitHub scan results."""
    console.print(f"\n[bold]{t('scan.github_header')}[/bold]")

    if not gh_result.available:
        console.print(f"  {t('scan.github_not_available')}")
        return

    if not gh_result.is_repo:
        console.print(f"  {t('scan.github_not_repo')}")
        return

    console.print(f"  {t('scan.github_issues', count=len(gh_result.issues))}")
    console.print(f"  {t('scan.github_prs', count=len(gh_result.pull_requests))}")
    console.print(f"  {t('scan.github_workflows', count=len(gh_result.workflows))}")

    if gh_result.issues:
        for issue in gh_result.issues[:5]:
            num = issue.get("number", "?")
            title = issue.get("title", "Untitled")
            console.print(f"    [dim]#{num}[/dim] {title}")
