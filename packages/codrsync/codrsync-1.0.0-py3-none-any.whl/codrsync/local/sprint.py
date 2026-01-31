"""
/sprint command - Sprint management

Works offline for status/close, interactive for planning.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
import questionary

from codrsync.config import require_project_context, ProjectContext
from codrsync.i18n import t


console = Console()


def show_status():
    """Show current sprint status"""
    ctx = require_project_context()
    sprint = ctx.manifest.get("current_sprint")

    if not sprint:
        console.print(t("sprint.no_active"))
        console.print(f"\n{t('sprint.start_hint')}")
        return

    number = sprint.get('number', '?')
    console.print("=" * 80)
    console.print(t("sprint.status_header", number=number).center(80))
    console.print("=" * 80)
    console.print()
    console.print(f"  {t('sprint.period', start=sprint.get('start'), end=sprint.get('end'))}")
    console.print(f"  {t('sprint.goal', goal=sprint.get('goal', t('sprint.goal_not_set')))}")
    console.print()

    # Stories
    stories = sprint.get("stories", [])
    if stories:
        total_points = sum(s.get("points", 0) for s in stories)
        done_points = sum(s.get("points", 0) for s in stories if s.get("status") == "done")

        console.print(f"  {t('sprint.points_delivered', done=done_points, total=total_points)}")
        console.print()
        console.print(f"  {t('sprint.stories_label')}")
        console.print("  " + "-" * 60)

        for s in stories:
            status_icon = {
                "done": "[green]✓[/green]",
                "in_progress": "[yellow]>[/yellow]",
                "pending": "[ ]",
                "todo": "[ ]"
            }.get(s.get("status", "pending"), "[ ]")

            console.print(
                f"  {status_icon} {s['id']}: {s['title'][:40]:<40} "
                f"{s.get('points', '-'):>3} pts  {s.get('status', 'pending').upper()}"
            )

    console.print()
    console.print("=" * 80)


def start(duration: int = 2, goal: Optional[str] = None):
    """Start a new sprint"""
    ctx = require_project_context()

    # Check for existing sprint
    current = ctx.manifest.get("current_sprint")
    if current:
        if not Confirm.ask(t("sprint.close_active_confirm", number=current.get('number'))):
            return

    # Calculate sprint number
    metrics = ctx.progress.get("metrics", {})
    completed_sprints = metrics.get("total_sprints_completed", 0)
    new_number = completed_sprints + 1

    # Get goal if not provided
    if not goal:
        goal = Prompt.ask(t("sprint.goal_prompt"), default=f"Sprint {new_number} goals")

    # Calculate dates
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(weeks=duration)).strftime("%Y-%m-%d")

    # Create sprint
    sprint = {
        "number": new_number,
        "goal": goal,
        "start": start_date,
        "end": end_date,
        "duration_weeks": duration,
        "stories": [],
        "status": "active"
    }

    ctx.manifest["current_sprint"] = sprint
    ctx.save()

    console.print()
    console.print(f"{t('common.success')} {t('sprint.started', number=new_number)}")
    console.print(f"  {t('sprint.started_period', start=start_date, end=end_date, duration=duration)}")
    console.print(f"  {t('sprint.started_goal', goal=goal)}")
    console.print()
    console.print(t("sprint.plan_next"))


def plan():
    """Interactive sprint planning"""
    ctx = require_project_context()
    sprint = ctx.manifest.get("current_sprint")

    if not sprint:
        console.print(f"{t('common.error')} {t('sprint.no_active_error')}")
        return

    # Get available stories from progress.json
    all_stories = ctx.progress.get("stories", [])
    available = [s for s in all_stories if s.get("status") in ["pending", "todo", None]]

    if not available:
        console.print(t("sprint.no_stories"))
        return

    console.print("=" * 80)
    console.print(t("sprint.planning_header").center(80))
    console.print("=" * 80)
    console.print()
    console.print(t("sprint.planning_info", number=sprint['number'], goal=sprint['goal']))
    console.print()

    # Show available stories
    console.print(t("sprint.available_stories"))
    console.print("-" * 60)

    choices = []
    for s in available:
        label = f"{s['id']}: {s['title'][:40]} ({s.get('points', '?')} pts)"
        choices.append({"name": label, "value": s["id"]})

    selected = questionary.checkbox(
        t("sprint.select_stories"),
        choices=choices
    ).ask()

    if not selected:
        console.print(t("sprint.no_selection"))
        return

    # Add selected stories to sprint
    sprint_stories = []
    total_points = 0

    for story_id in selected:
        story = next((s for s in all_stories if s["id"] == story_id), None)
        if story:
            sprint_stories.append({
                "id": story["id"],
                "title": story["title"],
                "points": story.get("points", 0),
                "status": "todo"
            })
            total_points += story.get("points", 0)

    sprint["stories"] = sprint_stories
    ctx.manifest["current_sprint"] = sprint
    ctx.save()

    console.print()
    console.print(f"{t('common.success')} {t('sprint.planned', count=len(sprint_stories), points=total_points)}")
    console.print()
    for s in sprint_stories:
        console.print(f"  - {s['id']}: {s['title']}")


def review():
    """Sprint review"""
    ctx = require_project_context()
    sprint = ctx.manifest.get("current_sprint")

    if not sprint:
        console.print(f"{t('common.error')} {t('sprint.no_active_review')}")
        return

    stories = sprint.get("stories", [])
    done = [s for s in stories if s.get("status") == "done"]
    not_done = [s for s in stories if s.get("status") != "done"]

    total_points = sum(s.get("points", 0) for s in stories)
    done_points = sum(s.get("points", 0) for s in done)
    completion = int(done_points / total_points * 100) if total_points else 0

    number = sprint['number']
    console.print("=" * 80)
    console.print(t("sprint.review_header", number=number).center(80))
    console.print("=" * 80)
    console.print()
    console.print(f"  {t('sprint.goal', goal=sprint['goal'])}")
    console.print(f"  {t('sprint.delivered', done=done_points, total=total_points, completion=completion)}")
    console.print()

    if done:
        console.print(f"  {t('sprint.completed_label')}")
        for s in done:
            console.print(f"    ✓ {s['id']}: {s['title']}")

    if not_done:
        console.print()
        console.print(f"  {t('sprint.not_completed_label')}")
        for s in not_done:
            console.print(f"    - {s['id']}: {s['title']} ({s.get('status', 'pending')})")

    console.print()
    console.print("=" * 80)


def retro():
    """Sprint retrospective"""
    ctx = require_project_context()
    sprint = ctx.manifest.get("current_sprint")

    if not sprint:
        console.print(f"{t('common.error')} {t('sprint.no_active_review')}")
        return

    number = sprint['number']
    console.print("=" * 80)
    console.print(t("sprint.retro_header", number=number).center(80))
    console.print("=" * 80)
    console.print()

    # What went well
    console.print(t("sprint.retro_went_well"))
    went_well = []
    while True:
        item = Prompt.ask("  +", default="")
        if not item:
            break
        went_well.append(item)

    # What could improve
    console.print()
    console.print(t("sprint.retro_improve"))
    could_improve = []
    while True:
        item = Prompt.ask("  -", default="")
        if not item:
            break
        could_improve.append(item)

    # Actions
    console.print()
    console.print(t("sprint.retro_actions"))
    actions = []
    while True:
        item = Prompt.ask("  →", default="")
        if not item:
            break
        actions.append(item)

    # Save retro
    sprint["retro"] = {
        "went_well": went_well,
        "could_improve": could_improve,
        "actions": actions,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    ctx.manifest["current_sprint"] = sprint
    ctx.save()

    console.print()
    console.print(f"{t('common.success')} {t('sprint.retro_saved')}")


def close():
    """Close current sprint"""
    ctx = require_project_context()
    sprint = ctx.manifest.get("current_sprint")

    if not sprint:
        console.print(f"{t('common.error')} {t('sprint.no_active_review')}")
        return

    if not Confirm.ask(t("sprint.close_confirm", number=sprint['number'])):
        return

    # Calculate metrics
    stories = sprint.get("stories", [])
    done_points = sum(s.get("points", 0) for s in stories if s.get("status") == "done")

    # Update metrics
    metrics = ctx.progress.get("metrics", {})
    velocity_history = metrics.get("velocity_history", [])
    velocity_history.append(done_points)

    metrics["velocity_history"] = velocity_history
    metrics["average_velocity"] = sum(velocity_history) / len(velocity_history)
    metrics["total_points_delivered"] = metrics.get("total_points_delivered", 0) + done_points
    metrics["total_sprints_completed"] = metrics.get("total_sprints_completed", 0) + 1

    ctx.progress["metrics"] = metrics

    # Move incomplete stories back to backlog
    incomplete = [s for s in stories if s.get("status") != "done"]
    if incomplete:
        console.print(f"  {t('sprint.moving_incomplete', count=len(incomplete))}")

    # Clear current sprint
    ctx.manifest["current_sprint"] = None
    ctx.save()

    console.print()
    console.print(f"{t('common.success')} {t('sprint.closed', number=sprint['number'])}")
    console.print(f"  {t('sprint.velocity', points=done_points)}")
    avg_vel = f"{metrics['average_velocity']:.1f}"
    console.print(f"  {t('sprint.average_velocity', avg=avg_vel)}")
