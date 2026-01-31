"""
/status command - Project dashboard

Works offline by reading local JSON files.
"""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn

from codrsync.config import require_project_context, ProjectContext
from codrsync.i18n import t


console = Console()


def calculate_health(ctx: ProjectContext) -> tuple[str, str]:
    """Calculate project health indicator"""
    blockers = ctx.progress.get("blockers", [])
    progress = ctx.overall_progress

    # Simple health calculation
    blocker_count = len(blockers)

    if blocker_count == 0 and progress >= 0:
        return "[green][====][/green]", t("status.health_good")
    elif blocker_count <= 2:
        return "[yellow][===!][/yellow]", t("status.health_warning")
    elif blocker_count <= 4:
        return "[orange1][==!!][/orange1]", t("status.health_at_risk")
    else:
        return "[red][!!!!][/red]", t("status.health_critical")


def render_progress_bar(progress: int, width: int = 20) -> str:
    """Render ASCII progress bar"""
    filled = int(width * progress / 100)
    empty = width - filled
    return f"|{'█' * filled}{'-' * empty}| {progress}%"


def run(mini: bool = False, prp: Optional[str] = None, executive: bool = False):
    """Run status command"""
    ctx = require_project_context()

    if mini:
        render_mini(ctx)
    elif prp:
        render_prp_status(ctx, prp)
    elif executive:
        render_executive(ctx)
    else:
        render_full(ctx)


def render_mini(ctx: ProjectContext):
    """One-line status"""
    health_icon, health_text = calculate_health(ctx)
    blockers = len(ctx.progress.get("blockers", []))
    if blockers:
        blocker_word = t("status.blocker_singular") if blockers == 1 else t("status.blocker_plural")
        blocker_text = f"{blockers} {blocker_word}"
    else:
        blocker_text = t("status.no_blockers_mini")

    console.print(
        f"{ctx.project_name} | {t('status.phase_label')} {ctx.phase} | {health_icon} | "
        f"{ctx.overall_progress}% | {blocker_text}"
    )


def render_full(ctx: ProjectContext):
    """Full dashboard"""
    health_icon, health_text = calculate_health(ctx)
    phases = ctx.progress.get("phases", {})
    epics = ctx.progress.get("epics", [])
    stories = ctx.progress.get("stories", [])
    blockers = ctx.progress.get("blockers", [])
    recent = ctx.progress.get("recent_activity", [])

    # Header
    console.print("=" * 80)
    console.print(f"{t('status.header'):^80}")
    console.print("=" * 80)
    console.print()
    console.print(f"  {t('status.project_label')} [bold]{ctx.project_name}[/bold]")
    console.print(f"  {t('status.phase_label')} {ctx.phase.title()}")
    console.print(f"  {t('status.health_label')} {health_icon} {health_text}")
    console.print()

    # Quick Stats
    console.print("-" * 80)
    console.print(f"{t('status.quick_stats'):^80}")
    console.print("-" * 80)
    console.print()
    console.print(f"  {t('status.overall_progress')}    {render_progress_bar(ctx.overall_progress)}")
    console.print()

    # Epic/Story counts
    epic_done = len([e for e in epics if e.get("status") == "done"])
    epic_active = len([e for e in epics if e.get("status") == "active"])
    epic_pending = len([e for e in epics if e.get("status") == "pending"])

    story_done = len([s for s in stories if s.get("status") == "done"])
    story_active = len([s for s in stories if s.get("status") in ["active", "in_progress"]])
    story_pending = len([s for s in stories if s.get("status") == "pending"])

    console.print(
        f"  {t('status.epics_label')}    {len(epics):2} {t('status.total')}   "
        f"{epic_done} {t('status.done')}, {epic_active} {t('status.active')}, {epic_pending} {t('status.pending')}"
    )
    console.print(
        f"  {t('status.stories_label')}  {len(stories):2} {t('status.total')}   "
        f"{story_done} {t('status.done')}, {story_active} {t('status.active')}, {story_pending} {t('status.pending')}"
    )
    console.print()

    # Current Focus
    console.print("-" * 80)
    console.print(f"{t('status.current_focus'):^80}")
    console.print("-" * 80)
    console.print()

    # Active PRPs
    prps = ctx.manifest.get("prps", [])
    active_prp = next((p for p in prps if p.get("status") in ["approved", "in_progress"]), None)
    if active_prp:
        console.print(f"  {t('status.active_prp')} [bold]{active_prp['id']}[/bold]: {active_prp['name']}")
        console.print(f"  {t('status.status_label')} {active_prp['status'].upper()}")
    console.print()

    # Blockers
    if blockers:
        console.print(f"  {t('status.blockers')}")
        for b in blockers[:3]:
            console.print(f"    ! {b.get('description', b)}")
    else:
        console.print(f"  {t('status.no_blockers')}")
    console.print()

    # Milestones
    console.print("-" * 80)
    console.print(f"{t('status.milestones'):^80}")
    console.print("-" * 80)
    console.print()

    milestones = ctx.manifest.get("milestones", [])
    for m in milestones[:5]:
        status_icon = "[x]" if m.get("status") == "done" else "[ ]"
        console.print(f"  {status_icon} {m['id']}: {m['name']:<30} {m.get('date', '')}    {m['status'].upper()}")
    console.print()

    # Recent Activity
    console.print("-" * 80)
    console.print(f"{t('status.recent_activity'):^80}")
    console.print("-" * 80)
    console.print()

    for activity in recent[-5:]:
        console.print(f"    + {activity.get('action', activity)}")
    console.print()

    # Footer
    console.print("=" * 80)
    console.print(f"  {t('status.footer', timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'))}")
    console.print("=" * 80)


def render_prp_status(ctx: ProjectContext, prp_id: str):
    """Status of specific PRP"""
    prps = ctx.manifest.get("prps", [])
    prp = next((p for p in prps if p.get("id") == prp_id), None)

    if not prp:
        console.print(f"{t('common.error')} {t('status.prp_not_found', prp_id=prp_id)}")
        return

    console.print("=" * 80)
    console.print(f"{prp['id']}: {prp['name']:^60}")
    console.print("=" * 80)
    console.print()
    console.print(f"  {t('status.status_label')} {prp['status'].upper()}")
    console.print(f"  {t('status.decisions_label')} {prp.get('decisions_count', '?')}")
    if prp.get("approved_at"):
        console.print(f"  {t('status.approved_label')} {prp['approved_at']}")
    console.print()
    console.print("=" * 80)


def render_executive(ctx: ProjectContext):
    """Executive summary"""
    health_icon, health_text = calculate_health(ctx)
    milestones = ctx.manifest.get("milestones", [])

    console.print("=" * 80)
    console.print(f"{t('status.executive_header'):^80}")
    console.print("=" * 80)
    console.print()
    console.print(f"  [bold]{ctx.project_name}[/bold] - {t('status.status_report')}")
    console.print(f"  {t('status.date_label')} {datetime.now().strftime('%Y-%m-%d')}")
    console.print()
    console.print(f"  {t('status.status_text')} {health_text} {health_icon}")
    console.print()
    console.print(f"  {t('status.progress_label')} {ctx.overall_progress}% {t('status.complete')}")
    console.print(f"  {t('status.phase_label')} {ctx.phase.title()}")
    console.print()

    # Upcoming milestones
    pending = [m for m in milestones if m.get("status") != "done"][:3]
    if pending:
        console.print(f"  {t('status.upcoming_milestones')}")
        for m in pending:
            console.print(f"    - {m['name']}: {m.get('date', 'TBD')}")
    console.print()
    console.print("=" * 80)
