"""
/roadmap command - Timeline and dependencies

Works offline by reading local JSON files.
"""

import json
from typing import Optional

from rich.console import Console

from codrsync.config import require_project_context, ProjectContext
from codrsync.i18n import t


console = Console()


def render_progress_bar(progress: int, width: int = 20) -> str:
    """Render ASCII progress bar"""
    filled = int(width * progress / 100)
    empty = width - filled
    return f"|{'█' * filled}{'-' * empty}| {progress:3}%"


def run(
    current: bool = False,
    epics: bool = False,
    mermaid: bool = False,
    json_output: bool = False
):
    """Run roadmap command"""
    ctx = require_project_context()

    if json_output:
        render_json(ctx)
    elif mermaid:
        render_mermaid(ctx)
    elif current:
        render_current_sprint(ctx)
    elif epics:
        render_epics(ctx)
    else:
        render_full(ctx)


def render_full(ctx: ProjectContext):
    """Full roadmap"""
    phases = ctx.progress.get("phases", {})
    epics_list = ctx.progress.get("epics", [])
    milestones = ctx.manifest.get("milestones", [])

    console.print("=" * 80)
    console.print(f"{ctx.project_name} - {t('roadmap.header')}".center(80))
    console.print("=" * 80)
    console.print()

    # Phases
    console.print("-" * 80)
    console.print(t("roadmap.phases_header").center(80))
    console.print("-" * 80)
    console.print()

    phase_order = ["discovery", "design", "development", "testing", "deploy", "launch"]
    phase_name_keys = {
        "discovery": "roadmap.phase_discovery",
        "design": "roadmap.phase_design",
        "development": "roadmap.phase_development",
        "testing": "roadmap.phase_testing",
        "deploy": "roadmap.phase_deploy",
        "launch": "roadmap.phase_launch",
    }

    for phase_key in phase_order:
        phase = phases.get(phase_key, {"status": "pending", "progress": 0})
        status = phase.get("status", "pending").upper()
        progress = phase.get("progress", 0)

        status_color = {
            "DONE": "green",
            "ACTIVE": "yellow",
            "PENDING": "dim"
        }.get(status, "dim")

        phase_name = t(phase_name_keys[phase_key])
        console.print(
            f"  [{status_color}]{phase_name:<15}[/{status_color}] "
            f"{status:<10} {render_progress_bar(progress)}"
        )

    console.print()

    # Epics
    if epics_list:
        console.print("-" * 80)
        console.print(t("roadmap.epics_header").center(80))
        console.print("-" * 80)
        console.print()
        console.print(
            f"  {t('roadmap.epic_col'):<30} {t('roadmap.status_col'):<12} "
            f"{t('roadmap.progress_col'):<25} {t('roadmap.dependencies_col')}"
        )
        console.print("  " + "-" * 76)

        for epic in epics_list:
            deps = ", ".join(epic.get("dependencies", [])) or "-"
            console.print(
                f"  {epic['id']}: {epic['name'][:20]:<20} "
                f"{epic['status'].upper():<12} "
                f"{render_progress_bar(epic.get('progress', 0)):<25} "
                f"{deps}"
            )

        console.print()

    # Milestones
    console.print("-" * 80)
    console.print(t("roadmap.milestones_header").center(80))
    console.print("-" * 80)
    console.print()

    for m in milestones:
        icon = "[x]" if m.get("status") == "done" else "[ ]"
        status_color = "green" if m.get("status") == "done" else "dim"
        console.print(
            f"  {icon} {m['id']}: {m['name']:<30} {m.get('date', 'TBD'):<12} "
            f"[{status_color}]{m['status'].upper()}[/{status_color}]"
        )

    console.print()
    console.print("=" * 80)


def render_current_sprint(ctx: ProjectContext):
    """Show only current sprint"""
    sprint = ctx.manifest.get("current_sprint")

    if not sprint:
        console.print(t("roadmap.no_active_sprint"))
        console.print(t("roadmap.start_sprint_hint"))
        return

    number = sprint.get('number', '?')
    console.print("-" * 80)
    console.print(t("roadmap.sprint_header", number=number).center(80))
    console.print("-" * 80)
    console.print()
    console.print(f"  {t('roadmap.period_label')} {sprint.get('start', '?')} - {sprint.get('end', '?')}")
    console.print(f"  {t('roadmap.goal_label')} {sprint.get('goal', t('sprint.goal_not_set'))}")
    console.print()

    stories = sprint.get("stories", [])
    if stories:
        console.print(f"  {t('roadmap.stories_label')}")
        for s in stories:
            status_icon = ">" if s.get("status") == "in_progress" else "-"
            console.print(f"    {status_icon} {s['id']}: {s['title']} ({s.get('status', 'pending')})")

    console.print()
    console.print("-" * 80)


def render_epics(ctx: ProjectContext):
    """Focus on epics"""
    epics_list = ctx.progress.get("epics", [])

    console.print(t("roadmap.epics_overview"))
    console.print()

    status_icons = {
        "done": "[green][DONE][/green]",
        "active": "[yellow][IN PROGRESS][/yellow]",
        "in_progress": "[yellow][IN PROGRESS][/yellow]",
        "blocked": "[red][BLOCKED][/red]",
        "pending": "[dim][PENDING][/dim]"
    }

    for epic in epics_list:
        icon = status_icons.get(epic.get("status", "pending"), "[PENDING]")
        console.print(f"{icon:20} {epic['id']}: {epic['name']}")

    console.print()

    # Dependencies
    console.print(t("roadmap.dependencies_label"))
    for epic in epics_list:
        deps = epic.get("dependencies", [])
        if deps:
            console.print(f"  {epic['id']} <- {', '.join(deps)}")


def render_mermaid(ctx: ProjectContext):
    """Output as Mermaid diagram"""
    phases = ctx.progress.get("phases", {})
    milestones = ctx.manifest.get("milestones", [])

    console.print("```mermaid")
    console.print("gantt")
    console.print(f"    title {ctx.project_name} {t('roadmap.header')}")
    console.print("    dateFormat  YYYY-MM-DD")

    phase_order = ["discovery", "design", "development", "testing", "deploy", "launch"]

    for i, phase_key in enumerate(phase_order):
        phase = phases.get(phase_key, {})
        status = "done" if phase.get("status") == "done" else "active" if phase.get("status") == "active" else ""
        status_str = f":{status}," if status else ":"

        console.print(f"    section Phase {i+1}")
        console.print(f"    {phase_key.title():<20}{status_str} p{i+1}, 2026-01-{10+i*5:02d}, 5d")

    console.print("```")


def render_json(ctx: ProjectContext):
    """Output as JSON"""
    data = {
        "project": ctx.project_name,
        "phase": ctx.phase,
        "overall_progress": ctx.overall_progress,
        "phases": ctx.progress.get("phases", {}),
        "epics": ctx.progress.get("epics", []),
        "milestones": ctx.manifest.get("milestones", []),
        "current_sprint": ctx.manifest.get("current_sprint"),
    }
    console.print(json.dumps(data, indent=2))
