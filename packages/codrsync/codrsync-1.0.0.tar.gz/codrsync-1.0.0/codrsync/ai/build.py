"""
/codrsync build - Execute development with AI guidance

Semi-autonomous: AI implements, pauses for important decisions.
Supports building from stories or full PRP execution.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from codrsync.auth import AIBackend
from codrsync.ai.backend import get_backend_instance
from codrsync.config import require_project_context
from codrsync.i18n import t


console = Console()


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

BUILD_STORY_SYSTEM = """\
You are codrsync, an AI development orchestrator implementing a user story.

Rules:
1. Analyze the story requirements carefully
2. Propose an implementation plan BEFORE writing code
3. For each file: show path, explain changes, then provide code
4. Flag any architectural decisions that need developer confirmation
5. After implementation, list files changed and next steps

Output format:
- Use Markdown with code blocks (specify language)
- Organize by implementation step
- Be precise about file paths relative to project root"""

BUILD_PRP_SYSTEM = """\
You are codrsync, an AI development orchestrator executing a PRP \
(Product Requirement Prompt).

Rules:
1. Parse the PRP to extract all stories and their requirements
2. For each story, generate a detailed implementation plan
3. Implement stories in dependency order
4. Pause at each story boundary for developer review
5. Track which stories are complete vs pending
6. Respect architectural decisions documented in the PRP

Output format for each story:
- Story ID and title
- Files to create/modify
- Implementation code
- Verification steps

When generating a plan, output JSON with this structure:
{
  "stories": [
    {
      "id": "STORY-XXX",
      "title": "...",
      "files": ["path/to/file.py", ...],
      "dependencies": ["STORY-YYY"],
      "plan": "Brief implementation description"
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(
    backend: AIBackend,
    prp: Optional[str] = None,
    story: Optional[str] = None,
):
    """Run build command"""
    ctx = require_project_context()

    console.print(Panel(
        f"{t('build.panel_title')}\n\n"
        f"{t('build.panel_description')}",
        border_style="blue",
    ))

    # Get AI backend
    ai = get_backend_instance(backend)

    # Determine what to build
    if story:
        console.print(f"\n{t('build.building_story', story_id=story)}")
        build_story(ai, ctx, story)
    elif prp:
        console.print(f"\n{t('build.executing_prp', prp_id=prp)}")
        build_prp(ai, ctx, prp)
    else:
        # Find current work
        sprint = ctx.manifest.get("current_sprint")
        if sprint and sprint.get("stories"):
            # Find first non-done story
            for s in sprint["stories"]:
                if s.get("status") != "done":
                    console.print(f"\n{t('build.continuing_story', story_id=s['id'])}")
                    build_story(ai, ctx, s["id"])
                    return

        console.print(t("build.no_active_work"))
        console.print(t("build.start_sprint_hint"))


# ---------------------------------------------------------------------------
# build story
# ---------------------------------------------------------------------------

def build_story(ai, ctx, story_id: str):
    """Build a specific story with AI guidance"""
    # Find story in progress
    stories = ctx.progress.get("stories", [])
    story = next((s for s in stories if s["id"] == story_id), None)

    if not story:
        console.print(f"{t('common.error')} {t('build.story_not_found', story_id=story_id)}")
        return

    console.print(f"\n[bold]{story['id']}[/bold]: {story.get('title', '')}")
    console.print(f"{t('build.points_label')} {story.get('points', '?')}")

    # Show acceptance criteria if available
    criteria = story.get("acceptance_criteria", [])
    if criteria:
        console.print(f"\n{t('build.acceptance_criteria')}")
        for c in criteria:
            console.print(f"  - {c}")

    console.print()

    # Build project context
    project_context = {
        "project_name": ctx.project_name,
        "tech_stack": ctx.manifest.get("project", {}).get("tech_stack", {}),
        "phase": ctx.phase,
    }

    # Read context file if it exists
    context_file = ctx.root / ".codrsync" / "context.md"
    context_content = ""
    if context_file.exists():
        context_content = context_file.read_text(encoding="utf-8")[:2000]

    # Build prompt
    prompt = f"""\
Implement this user story for the project: {ctx.project_name}

Story: {story['id']} - {story.get('title', '')}
Epic: {story.get('epic', '')}
Points: {story.get('points', '')}
Description: {story.get('description', '')}

Acceptance Criteria:
{chr(10).join('- ' + c for c in criteria) if criteria else 'Not specified'}

Tech Stack:
{json.dumps(project_context['tech_stack'], indent=2)}

{f'Project Context:{chr(10)}{context_content}' if context_content else ''}

Please:
1. First, propose an implementation plan (files to create/modify)
2. Then implement each file with complete code
3. Flag any decisions that need my confirmation
"""

    console.print(t("build.generating_plan"))
    console.print()

    try:
        for chunk in ai.run_interactive(prompt, system=BUILD_STORY_SYSTEM):
            console.print(chunk, end="")
        console.print()
    except Exception as e:
        console.print(f"\n{t('common.error')} {e}")
        return

    # Mark story as in-progress
    story["status"] = "in_progress"
    story["started_at"] = story.get("started_at", datetime.now().isoformat())
    ctx.save()

    # Ask if story is complete
    console.print()
    if Confirm.ask(t("build.mark_complete_confirm")):
        story["status"] = "done"
        story["completed_at"] = datetime.now().isoformat()
        ctx.save()

        _update_progress(ctx, story_id)

        console.print(f"\n{t('common.success')} {t('build.story_completed', story_id=story_id)}")
    else:
        console.print(t("build.story_continued"))


# ---------------------------------------------------------------------------
# build PRP
# ---------------------------------------------------------------------------

def build_prp(ai, ctx, prp_ref: str):
    """Execute a full PRP - parses stories and implements step by step"""

    # Resolve PRP: can be a file path or a PRP ID
    prp_path = _resolve_prp(ctx, prp_ref)

    if not prp_path or not prp_path.exists():
        console.print(f"{t('common.error')} {t('build.prp_not_found', prp_id=prp_ref)}")
        return

    # Read PRP content
    prp_content = prp_path.read_text(encoding="utf-8")

    console.print(Panel(
        f"[bold]{prp_path.stem}[/bold]\n\n"
        f"{t('build.prp_reading')}",
        border_style="blue",
    ))

    # Build project context
    project_context = {
        "project_name": ctx.project_name,
        "tech_stack": ctx.manifest.get("project", {}).get("tech_stack", {}),
    }

    # Read validation decisions if available
    validation_path = prp_path.with_name(prp_path.stem + "-validation.md")
    validation_content = ""
    if validation_path.exists():
        validation_content = validation_path.read_text(encoding="utf-8")

    # Phase 1: Generate execution plan
    console.print(f"\n{t('build.prp_phase1')}\n")

    plan_prompt = f"""\
Analyze this PRP and generate an execution plan.

PRP CONTENT:
---
{prp_content}
---

{f'VALIDATION DECISIONS:{chr(10)}{validation_content}' if validation_content else ''}

Extract all stories from the PRP and create an ordered execution plan.
Output as JSON with this structure:
{{
  "prp_name": "name of the PRP",
  "total_stories": N,
  "stories": [
    {{
      "id": "STORY-XXX",
      "title": "story title",
      "files": ["file1.py", "file2.py"],
      "dependencies": [],
      "points": N,
      "plan": "brief implementation description"
    }}
  ]
}}

IMPORTANT: Output ONLY the JSON, no markdown fences, no extra text.
"""

    try:
        plan_response = ai.run_prompt(
            plan_prompt,
            context=project_context,
            system=BUILD_PRP_SYSTEM,
        )
    except Exception as e:
        console.print(f"{t('common.error')} {e}")
        return

    # Parse execution plan
    plan = _parse_plan(plan_response)

    if not plan or not plan.get("stories"):
        console.print(f"{t('common.warning')} {t('build.prp_plan_failed')}")
        console.print(t("build.prp_fallback"))

        # Fallback: execute PRP as a whole
        _build_prp_fallback(ai, ctx, prp_content, project_context, validation_content)
        return

    # Display plan
    stories = plan["stories"]
    console.print(Panel(
        f"{t('build.prp_plan_ready', name=plan.get('prp_name', prp_path.stem))}",
        border_style="green",
    ))

    table = Table(title=t("build.prp_stories_title"))
    table.add_column("#", style="dim")
    table.add_column(t("prp.col_id"), style="cyan")
    table.add_column(t("prp.col_name"))
    table.add_column(t("build.col_files"))
    table.add_column(t("build.col_points"))

    for i, s in enumerate(stories, 1):
        table.add_row(
            str(i),
            s.get("id", f"STEP-{i}"),
            s.get("title", ""),
            str(len(s.get("files", []))),
            str(s.get("points", "?")),
        )

    console.print(table)

    total_points = sum(s.get("points", 0) for s in stories if isinstance(s.get("points"), int))
    console.print(f"\n{t('build.prp_total', count=len(stories), points=total_points)}")

    if not Confirm.ask(t("build.prp_start_confirm")):
        console.print(t("common.cancelled"))
        return

    # Update PRP status to in_progress
    _update_prp_status(ctx, prp_path.stem, "in_progress")

    # Register stories in progress.json if not already there
    _register_stories(ctx, stories, prp_path.stem)

    # Phase 2: Execute stories one by one
    console.print(f"\n{t('build.prp_phase2')}\n")

    completed = 0
    for i, story_plan in enumerate(stories, 1):
        story_id = story_plan.get("id", f"STEP-{i}")
        story_title = story_plan.get("title", "")

        console.print(Panel(
            f"[bold]{story_id}[/bold]: {story_title}\n"
            f"{t('build.prp_story_progress', current=i, total=len(stories))}",
            border_style="cyan",
        ))

        # Build story implementation prompt
        impl_prompt = f"""\
Implement this story from PRP {prp_path.stem}.

Story: {story_id} - {story_title}
Plan: {story_plan.get('plan', '')}
Files to create/modify: {', '.join(story_plan.get('files', []))}

Full PRP context (for reference):
---
{prp_content[:3000]}
---

{f'Validation decisions:{chr(10)}{validation_content[:1000]}' if validation_content else ''}

Please provide:
1. Implementation plan for this specific story
2. Complete code for each file
3. Any decisions that need confirmation
"""

        try:
            for chunk in ai.run_interactive(impl_prompt, system=BUILD_STORY_SYSTEM):
                console.print(chunk, end="")
            console.print()
        except Exception as e:
            console.print(f"\n{t('common.error')} {e}")

        # Checkpoint: ask developer to review
        console.print()
        choice = Prompt.ask(
            t("build.prp_story_choice"),
            choices=["continue", "skip", "stop"],
            default="continue",
        )

        if choice == "stop":
            console.print(t("build.prp_stopped"))
            break
        elif choice == "skip":
            console.print(t("build.prp_story_skipped", story_id=story_id))
            continue

        # Mark story as done
        completed += 1
        _mark_story_done(ctx, story_id)
        console.print(f"{t('common.success')} {t('build.story_completed', story_id=story_id)}")

    # Phase 3: Summary
    console.print(Panel(
        f"{t('build.prp_summary', completed=completed, total=len(stories))}\n\n"
        f"{t('build.prp_summary_remaining', remaining=len(stories) - completed)}",
        title=t("build.prp_summary_title"),
        border_style="green" if completed == len(stories) else "yellow",
    ))

    # Update PRP status
    if completed == len(stories):
        _update_prp_status(ctx, prp_path.stem, "done")
    _update_overall_progress(ctx)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_prp(ctx, prp_ref: str) -> Optional[Path]:
    """Resolve a PRP reference to a file path.

    Accepts: file path, PRP ID (e.g. PRP-01), or manifest index.
    """
    # Direct file path
    path = Path(prp_ref)
    if path.exists():
        return path

    # Try as PRP ID from manifest
    for prp in ctx.manifest.get("prps", []):
        if prp.get("id") == prp_ref or prp_ref in prp.get("id", ""):
            prp_file = prp.get("file")
            if prp_file:
                p = Path(prp_file)
                if p.exists():
                    return p

    # Try PRPs directory
    prps_dir = ctx.root / "PRPs"
    if prps_dir.exists():
        for f in prps_dir.glob("PRP-*.md"):
            if prp_ref in f.stem:
                return f

    return None


def _parse_plan(response: str) -> Optional[dict]:
    """Parse AI response as JSON execution plan."""
    # Try direct JSON parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in response
    brace_match = re.search(r"\{.*\}", response, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _build_prp_fallback(ai, ctx, prp_content, project_context, validation_content):
    """Fallback: execute PRP as a single prompt when plan parsing fails"""
    prompt = f"""\
Execute this PRP. Implement all stories described in it.

PRP CONTENT:
---
{prp_content}
---

{f'Validation decisions:{chr(10)}{validation_content}' if validation_content else ''}

For each story:
1. Show the story ID and title
2. List files to create/modify
3. Provide complete implementation code
4. Explain what was done
"""

    console.print(f"\n{t('build.prp_executing_full')}\n")

    try:
        for chunk in ai.run_interactive(prompt, system=BUILD_PRP_SYSTEM):
            console.print(chunk, end="")
        console.print()
    except Exception as e:
        console.print(f"\n{t('common.error')} {e}")


def _register_stories(ctx, stories: list, prp_stem: str):
    """Register PRP stories into progress.json"""
    existing_ids = {s["id"] for s in ctx.progress.get("stories", [])}

    for s in stories:
        story_id = s.get("id", "")
        if story_id and story_id not in existing_ids:
            ctx.progress.setdefault("stories", []).append({
                "id": story_id,
                "title": s.get("title", ""),
                "epic": prp_stem,
                "points": s.get("points", 0),
                "status": "pending",
                "description": s.get("plan", ""),
                "acceptance_criteria": [],
            })

    ctx.save()


def _mark_story_done(ctx, story_id: str):
    """Mark a story as done in progress.json"""
    for s in ctx.progress.get("stories", []):
        if s["id"] == story_id:
            s["status"] = "done"
            s["completed_at"] = datetime.now().isoformat()
            break
    ctx.save()


def _update_prp_status(ctx, prp_stem: str, status: str):
    """Update PRP status in manifest"""
    for prp in ctx.manifest.get("prps", []):
        if prp_stem.startswith(prp.get("id", "")):
            prp["status"] = status
            if status == "done":
                prp["completed_at"] = datetime.now().isoformat()
            break
    ctx.manifest["last_updated"] = datetime.now().isoformat()
    ctx.save()


def _update_progress(ctx, story_id: str):
    """Update overall progress after completing a story"""
    stories = ctx.progress.get("stories", [])
    if not stories:
        return

    done_count = sum(1 for s in stories if s.get("status") == "done")
    total = len(stories)
    progress_pct = int((done_count / total) * 100) if total > 0 else 0

    ctx.progress["overall_progress"] = progress_pct

    ctx.progress.setdefault("recent_activity", []).insert(0, {
        "date": datetime.now().isoformat(),
        "action": f"Story {story_id} completed",
    })

    ctx.save()


def _update_overall_progress(ctx):
    """Recalculate overall progress from stories"""
    stories = ctx.progress.get("stories", [])
    if not stories:
        return

    done_count = sum(1 for s in stories if s.get("status") == "done")
    total = len(stories)
    progress_pct = int((done_count / total) * 100) if total > 0 else 0

    ctx.progress["overall_progress"] = progress_pct
    ctx.progress["last_updated"] = datetime.now().isoformat()
    ctx.save()
