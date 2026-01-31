"""
codrsync doctor - Diagnostic checks
"""

import sys
import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table

from codrsync import __version__
from codrsync.auth import detect_claude_code, detect_anthropic_api, get_ai_backend
from codrsync.config import get_project_context, CODRSYNC_CONFIG
from codrsync.i18n import t


console = Console()


def run_diagnostics():
    """Run all diagnostic checks"""
    console.print(f"\n{t('doctor.title', version=__version__)}\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column(t("doctor.col_check"), style="cyan")
    table.add_column(t("doctor.col_status"))
    table.add_column(t("doctor.col_details"))

    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    table.add_row(
        t("doctor.python_version"),
        "[green]✓[/green]" if py_ok else "[red]✗[/red]",
        f"{py_version} {t('doctor.python_ok') if py_ok else t('doctor.python_need')}"
    )

    # Claude Code
    has_claude = detect_claude_code()
    claude_path = shutil.which("claude") or t("doctor.not_found") if hasattr(t, '__call__') else "not found"
    table.add_row(
        t("doctor.claude_code"),
        "[green]✓[/green]" if has_claude else "[yellow]○[/yellow]",
        (shutil.which("claude") or "") if has_claude else t("doctor.not_installed_optional")
    )

    # Anthropic API
    has_api = detect_anthropic_api()
    table.add_row(
        t("doctor.anthropic_api_key"),
        "[green]✓[/green]" if has_api else "[yellow]○[/yellow]",
        t("doctor.configured") if has_api else t("doctor.not_set_optional")
    )

    # AI Backend
    backend = get_ai_backend()
    table.add_row(
        t("doctor.active_backend"),
        "[green]✓[/green]" if backend.value != "offline" else "[yellow]○[/yellow]",
        backend.value
    )

    # Config file
    has_config = CODRSYNC_CONFIG.exists()
    table.add_row(
        t("doctor.config_file"),
        "[green]✓[/green]" if has_config else "[dim]○[/dim]",
        str(CODRSYNC_CONFIG) if has_config else t("doctor.not_created")
    )

    # Current project
    ctx = get_project_context()
    if ctx:
        table.add_row(
            t("doctor.project_detected"),
            "[green]✓[/green]",
            ctx.project_name
        )
    else:
        table.add_row(
            t("doctor.project_detected"),
            "[dim]○[/dim]",
            t("doctor.no_project")
        )

    # Dependencies
    deps_ok = True
    missing_deps = []

    try:
        import typer
    except ImportError:
        deps_ok = False
        missing_deps.append("typer")

    try:
        import rich
    except ImportError:
        deps_ok = False
        missing_deps.append("rich")

    try:
        import questionary
    except ImportError:
        deps_ok = False
        missing_deps.append("questionary")

    try:
        import openpyxl
    except ImportError:
        missing_deps.append("openpyxl (for Excel export)")

    table.add_row(
        t("doctor.dependencies"),
        "[green]✓[/green]" if deps_ok else "[red]✗[/red]",
        t("doctor.all_installed") if not missing_deps else t("doctor.missing", deps=", ".join(missing_deps))
    )

    console.print(table)
    console.print()

    # Summary
    if backend.value == "offline":
        console.print(f"{t('common.note')} {t('doctor.ai_disabled_note')}\n")

    if not ctx:
        console.print(f"{t('common.tip')} {t('doctor.init_tip')}\n")
