"""
codrsync CLI - Main entry point

Commands:
  Local (no AI needed):
    - status: Show project dashboard
    - roadmap: Show timeline and dependencies
    - export: Export to Excel/Jira/Trello/Notion
    - sprint: Manage sprints
    - scan: Detect project stack, docs, and GitHub info
    - connect: Check integration status for external services

  AI-powered (uses Claude Code or API):
    - init: Initialize new project (kickstart wizard)
    - build: Execute development with AI guidance
    - prp: Generate or execute PRPs
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from codrsync import __version__
from codrsync.config import get_config, Config, is_first_run
from codrsync.auth import get_ai_backend, AIBackend
from codrsync.i18n import lazy_t, t

# Sub-modules
from codrsync.local import status as status_module
from codrsync.local import roadmap as roadmap_module
from codrsync.local import export as export_module
from codrsync.local import sprint as sprint_module
from codrsync.ai import kickstart as kickstart_module
from codrsync.scanner import scan as scan_module
from codrsync.connect import connect as connect_module

app = typer.Typer(
    name="codrsync",
    help=lazy_t("cli.app.help"),
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool):
    if value:
        console.print(t("cli.version.show", version=__version__))
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help=lazy_t("cli.version.help")
    ),
):
    """
    [bold cyan]codrsync[/bold cyan] - Turn any dev into jedi ninja codr

    AI-powered development orchestrator with guided development,
    interactive validation, and persistent context.
    """
    if is_first_run():
        from codrsync.onboarding import run_onboarding
        run_onboarding()


# =============================================================================
# LOCAL COMMANDS (No AI needed)
# =============================================================================

@app.command(help=lazy_t("cli.status.help"), rich_help_panel=lazy_t("cli.panel.local"))
def status(
    mini: bool = typer.Option(False, "--mini", "-m", help=lazy_t("cli.status.mini_help")),
    prp: str = typer.Option(None, "--prp", "-p", help=lazy_t("cli.status.prp_help")),
    executive: bool = typer.Option(False, "--executive", "-e", help=lazy_t("cli.status.executive_help")),
):
    status_module.run(mini=mini, prp=prp, executive=executive)


@app.command(help=lazy_t("cli.roadmap.help"), rich_help_panel=lazy_t("cli.panel.local"))
def roadmap(
    current: bool = typer.Option(False, "--current", "-c", help=lazy_t("cli.roadmap.current_help")),
    epics: bool = typer.Option(False, "--epics", "-e", help=lazy_t("cli.roadmap.epics_help")),
    mermaid: bool = typer.Option(False, "--mermaid", help=lazy_t("cli.roadmap.mermaid_help")),
    json_output: bool = typer.Option(False, "--json", "-j", help=lazy_t("cli.roadmap.json_help")),
):
    roadmap_module.run(current=current, epics=epics, mermaid=mermaid, json_output=json_output)


@app.command(help=lazy_t("cli.export.help"), rich_help_panel=lazy_t("cli.panel.local"))
def export(
    format: str = typer.Argument("excel", help=lazy_t("cli.export.format_help")),
    output: str = typer.Option("exports", "--output", "-o", help=lazy_t("cli.export.output_help")),
):
    export_module.run(format=format, output=output)


# Sprint subcommands
sprint_app = typer.Typer(help=lazy_t("cli.sprint.help"), rich_markup_mode="rich")
app.add_typer(sprint_app, name="sprint", rich_help_panel=lazy_t("cli.panel.local"))


@sprint_app.callback(invoke_without_command=True)
def sprint_status(ctx: typer.Context):
    """Show current sprint status (default when no subcommand)."""
    if ctx.invoked_subcommand is None:
        sprint_module.show_status()


@sprint_app.command("start")
def sprint_start(
    duration: int = typer.Option(2, "--duration", "-d", help=lazy_t("cli.sprint.duration_help")),
    goal: str = typer.Option(None, "--goal", "-g", help=lazy_t("cli.sprint.goal_help")),
):
    """Start a new sprint."""
    sprint_module.start(duration=duration, goal=goal)


@sprint_app.command("plan")
def sprint_plan():
    """Interactive sprint planning."""
    sprint_module.plan()


@sprint_app.command("review")
def sprint_review():
    """Sprint review - summarize deliveries."""
    sprint_module.review()


@sprint_app.command("retro")
def sprint_retro():
    """Sprint retrospective - capture learnings."""
    sprint_module.retro()


@sprint_app.command("close")
def sprint_close():
    """Close current sprint."""
    sprint_module.close()


@app.command(help=lazy_t("cli.scan.help"), rich_help_panel=lazy_t("cli.panel.local"))
def scan(
    path: str = typer.Argument(None, help=lazy_t("cli.scan.path_help")),
    github: bool = typer.Option(False, "--github", "-g", help=lazy_t("cli.scan.github_help")),
    docs: bool = typer.Option(False, "--docs", "-d", help=lazy_t("cli.scan.docs_help")),
    deep: bool = typer.Option(False, "--deep", help=lazy_t("cli.scan.deep_help")),
):
    backend = None
    if deep:
        from codrsync.ai.backend import get_backend_instance
        ai_backend = get_ai_backend()
        if ai_backend != AIBackend.OFFLINE:
            backend = get_backend_instance(ai_backend)
        else:
            console.print(f"{t('common.warning')} {t('common.ai_required_short')}")

    scan_module.run(
        path=Path(path) if path else None,
        github=github,
        docs=docs,
        deep=deep,
        backend=backend,
    )


@app.command(help=lazy_t("cli.connect.help"), rich_help_panel=lazy_t("cli.panel.local"))
def connect(
    service: str = typer.Argument(None, help=lazy_t("cli.connect.service_help")),
    path: str = typer.Argument(None, help=lazy_t("cli.connect.path_help")),
):
    connect_module.run(
        service=service,
        path=Path(path) if path else None,
    )


# =============================================================================
# AI-POWERED COMMANDS
# =============================================================================

@app.command(help=lazy_t("cli.init.help"), rich_help_panel=lazy_t("cli.panel.ai"))
def init(
    name: str = typer.Option(None, "--name", "-n", help=lazy_t("cli.init.name_help")),
    skip_research: bool = typer.Option(False, "--skip-research", help=lazy_t("cli.init.skip_research_help")),
):
    backend = get_ai_backend()

    if backend == AIBackend.OFFLINE:
        console.print(Panel(
            t("common.ai_required"),
            title=t("common.ai_required_title"),
            border_style="yellow"
        ))
        raise typer.Exit(1)

    # Check for existing code → offer import
    from codrsync.scanner.detector import has_existing_code
    project_path = Path.cwd()

    if has_existing_code(project_path) and not Path("doc/project/manifest.json").exists():
        console.print(Panel(
            f"{t('init.existing_detected')}\n\n{t('init.existing_description')}",
            border_style="yellow",
        ))

        import questionary
        choice = questionary.select(
            t("init.existing_detected"),
            choices=[
                {"name": t("init.choice_import"), "value": "import"},
                {"name": t("init.choice_fresh"), "value": "fresh"},
            ]
        ).ask()

        if choice == "import":
            console.print(f"\n  {t('init.import_scan_step')}")
            scan_result = scan_module.run(
                path=project_path, github=True, docs=True,
            )
            console.print(f"  {t('init.import_connect_step')}")
            connect_module.run(path=project_path)
            console.print(f"  {t('init.import_context_step')}")
            kickstart_module.run_from_scan(backend=backend, scan_result=scan_result)
            return

    kickstart_module.run(backend=backend, name=name, skip_research=skip_research)


@app.command(help=lazy_t("cli.build.help"), rich_help_panel=lazy_t("cli.panel.ai"))
def build(
    prp: str = typer.Argument(None, help=lazy_t("cli.build.prp_help")),
    story: str = typer.Option(None, "--story", "-s", help=lazy_t("cli.build.story_help")),
):
    backend = get_ai_backend()

    if backend == AIBackend.OFFLINE:
        console.print(f"{t('common.error')} {t('common.ai_required_short')}")
        raise typer.Exit(1)

    from codrsync.ai import build as build_module
    build_module.run(backend=backend, prp=prp, story=story)


@app.command(help=lazy_t("cli.prp.help"), rich_help_panel=lazy_t("cli.panel.ai"))
def prp(
    action: str = typer.Argument("list", help=lazy_t("cli.prp.action_help")),
    file: str = typer.Argument(None, help=lazy_t("cli.prp.file_help")),
):
    from codrsync.ai import prp as prp_module
    prp_module.run(action=action, file=file)


@app.command(help=lazy_t("cli.auth.help"), rich_help_panel=lazy_t("cli.panel.config"))
def auth(
    show: bool = typer.Option(False, "--show", "-s", help=lazy_t("cli.auth.show_help")),
    cloud: bool = typer.Option(False, "--cloud", "-c", help=lazy_t("cli.auth.cloud_help")),
    logout: bool = typer.Option(False, "--logout", help=lazy_t("cli.auth.logout_help")),
):
    from codrsync.auth import configure_auth, show_auth_status

    if cloud:
        from codrsync.cloud_auth import cloud_login
        cloud_login()
    elif logout:
        from codrsync.cloud_auth import cloud_logout
        cloud_logout()
    elif show:
        show_auth_status()
    else:
        configure_auth()


# =============================================================================
# CLOUD STORAGE COMMANDS
# =============================================================================

storage_app = typer.Typer(help=lazy_t("cli.storage.help"), rich_markup_mode="rich")
app.add_typer(storage_app, name="storage", rich_help_panel=lazy_t("cli.panel.config"))


@storage_app.command("upload", help=lazy_t("cli.storage.upload_help"))
def storage_upload(
    file: str = typer.Argument(..., help=lazy_t("cli.storage.file_help")),
    folder: str = typer.Option("uploads", "--folder", "-f", help=lazy_t("cli.storage.folder_help")),
    public: bool = typer.Option(False, "--public", "-p", help=lazy_t("cli.storage.public_help")),
):
    from codrsync.cloud.storage import upload_file, StorageError, StorageLimitExceeded

    try:
        result = upload_file(file, folder=folder, is_public=public)
        if result.get("usage"):
            usage = result["usage"]
            console.print(f"\n[dim]Storage: {usage.get('used', '?')} / {usage.get('limit', '?')} ({usage.get('percentUsed', 0)}%)[/dim]")
    except StorageLimitExceeded as e:
        console.print(Panel(
            f"{t('cloud_storage.limit_exceeded', used=e.usage.get('used', '?'), limit=e.usage.get('limit', '?'))}\n\n"
            f"{t('cloud_storage.upgrade_hint', plan='Pro')}",
            title=t("common.error"),
            border_style="red",
        ))
        raise typer.Exit(1)
    except StorageError as e:
        console.print(f"{t('common.error')} {str(e)}")
        raise typer.Exit(1)


@storage_app.command("download", help=lazy_t("cli.storage.download_help"))
def storage_download(
    key: str = typer.Argument(..., help=lazy_t("cli.storage.key_help")),
    output: str = typer.Option(None, "--output", "-o", help=lazy_t("cli.storage.output_help")),
):
    from codrsync.cloud.storage import download_file, StorageError

    try:
        download_file(key, output_path=output)
    except StorageError as e:
        console.print(f"{t('common.error')} {str(e)}")
        raise typer.Exit(1)


@storage_app.command("list", help=lazy_t("cli.storage.list_help"))
def storage_list(
    folder: str = typer.Option(None, "--folder", "-f", help=lazy_t("cli.storage.folder_help")),
):
    from codrsync.cloud.storage import list_files, StorageError
    from rich.table import Table

    try:
        files = list_files(folder=folder)

        if not files:
            console.print("[dim]No files found.[/dim]")
            return

        table = Table(title="Cloud Storage Files")
        table.add_column("Filename", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Folder")
        table.add_column("Created")

        for f in files:
            size = f.get("size", 0)
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
            table.add_row(
                f.get("filename", "?"),
                size_str,
                f.get("folder", ""),
                f.get("created_at", "")[:10] if f.get("created_at") else "",
            )

        console.print(table)
    except StorageError as e:
        console.print(f"{t('common.error')} {str(e)}")
        raise typer.Exit(1)


@storage_app.command("delete", help=lazy_t("cli.storage.delete_help"))
def storage_delete(
    key: str = typer.Argument(..., help=lazy_t("cli.storage.key_help")),
):
    from codrsync.cloud.storage import delete_file, StorageError

    try:
        delete_file(key)
    except StorageError as e:
        console.print(f"{t('common.error')} {str(e)}")
        raise typer.Exit(1)


@storage_app.command("usage", help=lazy_t("cli.storage.usage_help"))
def storage_usage():
    from codrsync.cloud.storage import get_usage, StorageError
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn

    try:
        data = get_usage()

        console.print(f"\n[bold]Storage Usage[/bold] ({data.get('tier', 'free').title()} plan)\n")

        used = data.get("usage", {}).get("formatted", "0 B")
        limit = data.get("limit", {}).get("formatted", "100 MB")
        percent = data.get("percentUsed", 0)
        file_count = data.get("usage", {}).get("fileCount", 0)

        # Progress bar
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"{used} / {limit}", total=100, completed=percent)
            progress.refresh()

        console.print(f"  Used: [cyan]{used}[/cyan] of [cyan]{limit}[/cyan]")
        console.print(f"  Files: [cyan]{file_count}[/cyan]")
        console.print(f"  Remaining: [green]{data.get('remaining', {}).get('formatted', '?')}[/green]")

        if percent > 80:
            console.print(f"\n[yellow]{t('cloud_storage.upgrade_hint', plan='Pro')}[/yellow]")

    except StorageError as e:
        console.print(f"{t('common.error')} {str(e)}")
        raise typer.Exit(1)


# =============================================================================
# UTILITY COMMANDS
# =============================================================================

@app.command(help=lazy_t("cli.doctor.help"), rich_help_panel=lazy_t("cli.panel.config"))
def doctor():
    from codrsync.utils.doctor import run_diagnostics
    run_diagnostics()


if __name__ == "__main__":
    app()
