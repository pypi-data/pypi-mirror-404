"""
/codrsync prp - Manage PRPs (Product Requirement Prompts)

Actions:
  - list: Show all PRPs and their status
  - generate: Create PRP from INITIAL.md using AI
  - validate: Interactive validation loop with AI
  - execute: Execute approved PRP (delegates to build)
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

from codrsync.auth import AIBackend, get_ai_backend
from codrsync.ai.backend import get_backend_instance
from codrsync.config import require_project_context, get_project_context, Config
from codrsync.i18n import t


console = Console()


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

PRP_GENERATE_SYSTEM = """\
You are codrsync, an AI development orchestrator specialized in creating \
Product Requirement Prompts (PRPs).

A PRP is a structured specification document that bridges business \
requirements and AI-executable development tasks. It contains:

1. **Header**: ID, name, version, status, dates
2. **Objective**: Clear description of what will be built
3. **Context**: Existing codebase, tech stack, constraints
4. **Requirements**: Functional and non-functional requirements
5. **Architecture**: Proposed solution design
6. **Stories**: Broken-down implementation tasks (user stories)
7. **Decisions**: Key architectural decisions (numbered)
8. **Acceptance Criteria**: How to verify completion
9. **Risks**: Potential issues and mitigations

Output the PRP in Markdown format. Use the structure above with clear \
sections using ## headings. Each story should have an ID (STORY-XXX), \
title, description, points estimate (1-8), and acceptance criteria.

Respond ONLY with the PRP Markdown content. Do not add preamble."""

PRP_VALIDATE_SYSTEM = """\
You are codrsync, an AI development orchestrator conducting interactive \
validation of a Product Requirement Prompt (PRP).

Your role is to review the PRP and ask critical questions about:
- Architecture decisions that need confirmation
- Technology choices that have trade-offs
- Scope boundaries that need clarification
- Risk areas that need mitigation plans
- Missing requirements or edge cases

For each question:
1. Explain WHY this decision matters
2. Present 2-3 options with trade-offs
3. Give your recommendation
4. Ask the developer to confirm or choose

After all questions are answered, provide a summary of decisions made \
and mark the PRP as validated.

Keep questions focused and actionable. Aim for 3-7 critical questions."""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(action: str = "list", file: Optional[str] = None):
    """Run PRP command"""
    if action == "list":
        list_prps()
    elif action == "generate":
        generate_prp(file)
    elif action == "validate":
        validate_prp(file)
    elif action == "execute":
        execute_prp(file)
    else:
        console.print(f"{t('common.error')} {t('prp.unknown_action', action=action)}")
        console.print(t("prp.available_actions"))


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def list_prps():
    """List all PRPs from manifest and filesystem"""
    ctx = get_project_context()

    if not ctx:
        console.print(t("prp.no_project"))
        return

    prps = ctx.manifest.get("prps", [])

    # Also scan PRPs/ directory for files not yet in manifest
    prps_dir = ctx.root / "PRPs"
    fs_prps = []
    if prps_dir.exists():
        for f in sorted(prps_dir.glob("PRP-*.md")):
            prp_id = f.stem  # e.g. PRP-01-feature
            if not any(p.get("id") == prp_id for p in prps):
                fs_prps.append({"id": prp_id, "name": f.stem, "status": "draft", "file": str(f)})

    all_prps = prps + fs_prps

    if not all_prps:
        console.print(t("prp.no_prps"))
        console.print(t("prp.create_hint"))
        return

    table = Table(title=t("prp.table_title"))
    table.add_column(t("prp.col_id"), style="cyan")
    table.add_column(t("prp.col_name"))
    table.add_column(t("prp.col_status"))
    table.add_column(t("prp.col_decisions"))
    table.add_column(t("prp.col_approved"))

    status_colors = {
        "draft": "dim",
        "pending": "yellow",
        "validated": "blue",
        "approved": "green",
        "in_progress": "blue",
        "done": "green",
    }

    for prp in all_prps:
        status = prp.get("status", "draft")
        status_color = status_colors.get(status, "white")

        table.add_row(
            prp.get("id", ""),
            prp.get("name", ""),
            f"[{status_color}]{status.upper()}[/{status_color}]",
            str(prp.get("decisions_count", "-")),
            prp.get("approved_at", "-"),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def generate_prp(initial_file: Optional[str]):
    """Generate PRP from an INITIAL.md requirements document"""
    if not initial_file:
        console.print(f"{t('common.error')} {t('prp.specify_initial')}")
        console.print(t("prp.usage_generate"))
        return

    initial_path = Path(initial_file)
    if not initial_path.exists():
        console.print(f"{t('common.error')} {t('prp.file_not_found', file=initial_file)}")
        return

    backend = get_ai_backend()
    if backend == AIBackend.OFFLINE:
        console.print(f"{t('common.error')} {t('prp.ai_required')}")
        console.print(t("prp.auth_hint"))
        return

    ctx = get_project_context()

    # Read initial requirements
    initial_content = initial_path.read_text(encoding="utf-8")

    console.print(Panel(
        f"{t('prp.generating_from', file=initial_file)}\n\n"
        f"{t('prp.generate_reading_initial')}",
        border_style="cyan",
    ))

    # Build context from project data
    project_context = {}
    if ctx:
        project_context = {
            "project_name": ctx.project_name,
            "tech_stack": ctx.manifest.get("project", {}).get("tech_stack", {}),
            "phase": ctx.phase,
            "existing_prps": [
                {"id": p.get("id"), "name": p.get("name")}
                for p in ctx.manifest.get("prps", [])
            ],
            "existing_stories": len(ctx.progress.get("stories", [])),
        }

    # Determine next PRP ID
    existing_prps = ctx.manifest.get("prps", []) if ctx else []
    next_num = len(existing_prps) + 1

    # Also check filesystem for higher numbers
    prps_dir = Path("PRPs")
    if prps_dir.exists():
        for f in prps_dir.glob("PRP-*.md"):
            match = re.match(r"PRP-(\d+)", f.stem)
            if match:
                num = int(match.group(1))
                if num >= next_num:
                    next_num = num + 1

    prp_id = f"PRP-{next_num:02d}"

    # Build generation prompt
    prompt = f"""\
Generate a complete PRP (Product Requirement Prompt) from the following \
initial requirements document.

PRP ID: {prp_id}

INITIAL REQUIREMENTS:
---
{initial_content}
---

Generate a comprehensive PRP with:
- Clear objective and context
- Functional and non-functional requirements
- Proposed architecture
- User stories (STORY-{next_num:02d}01 through STORY-{next_num:02d}XX) with point estimates
- Key architectural decisions (numbered D1, D2, etc.)
- Acceptance criteria
- Risks and mitigations

Use the project context provided to tailor the PRP to the existing codebase.
"""

    console.print(f"\n{t('prp.generate_calling_ai')}\n")

    ai = get_backend_instance(backend)

    try:
        response = ai.run_prompt(prompt, context=project_context, system=PRP_GENERATE_SYSTEM)
    except Exception as e:
        console.print(f"{t('common.error')} {t('prp.generate_failed', error=str(e))}")
        return

    if not response or response.startswith("Error:"):
        console.print(f"{t('common.error')} {t('prp.generate_failed', error=response)}")
        return

    # Ensure PRPs directory exists
    prps_dir.mkdir(parents=True, exist_ok=True)

    # Derive a slug from the initial file name
    slug = initial_path.stem.lower().replace("initial", "").strip("-_ ")
    if not slug:
        slug = "feature"
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")

    prp_filename = f"{prp_id}-{slug}.md"
    prp_path = prps_dir / prp_filename

    # Write PRP file
    prp_path.write_text(response, encoding="utf-8")

    console.print(Panel(
        f"{t('common.success')} {t('prp.generate_saved', file=str(prp_path))}\n\n"
        f"{t('prp.generate_next_step', prp_file=str(prp_path))}",
        title=prp_id,
        border_style="green",
    ))

    # Register in manifest
    if ctx:
        prp_entry = {
            "id": prp_id,
            "name": slug.replace("-", " ").title(),
            "file": str(prp_path),
            "status": "pending",
            "decisions_count": 0,
            "created_at": datetime.now().isoformat(),
            "approved_at": None,
        }
        ctx.manifest.setdefault("prps", []).append(prp_entry)
        ctx.manifest["last_updated"] = datetime.now().isoformat()
        ctx.save()

        # Log activity
        ctx.progress.setdefault("recent_activity", []).insert(0, {
            "date": datetime.now().isoformat(),
            "action": f"PRP {prp_id} generated from {initial_path.name}",
        })
        ctx.save()


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def validate_prp(prp_file: Optional[str]):
    """Interactive validation session for a PRP"""
    if not prp_file:
        console.print(f"{t('common.error')} {t('prp.specify_prp')}")
        console.print(t("prp.usage_validate"))
        return

    prp_path = Path(prp_file)
    if not prp_path.exists():
        console.print(f"{t('common.error')} {t('prp.file_not_found', file=prp_file)}")
        return

    backend = get_ai_backend()
    if backend == AIBackend.OFFLINE:
        console.print(f"{t('common.error')} {t('prp.ai_required')}")
        return

    ctx = get_project_context()

    # Read PRP content
    prp_content = prp_path.read_text(encoding="utf-8")

    console.print(Panel(
        f"{t('prp.validate_title')}\n\n"
        f"{t('prp.validate_description')}",
        border_style="yellow",
    ))

    # Build context
    project_context = {}
    if ctx:
        project_context = {
            "project_name": ctx.project_name,
            "tech_stack": ctx.manifest.get("project", {}).get("tech_stack", {}),
        }

    # Start validation conversation
    ai = get_backend_instance(backend)

    initial_prompt = f"""\
Review this PRP and identify the critical decisions that need validation \
from the developer. Ask your first question.

PRP CONTENT:
---
{prp_content}
---

Start with the most important architectural decision that needs confirmation.
"""

    console.print(f"\n{t('prp.validate_analyzing')}\n")

    try:
        response = ai.run_prompt(
            initial_prompt,
            context=project_context,
            system=PRP_VALIDATE_SYSTEM,
        )
    except Exception as e:
        console.print(f"{t('common.error')} {e}")
        return

    # Interactive validation loop
    messages = [
        {"role": "user", "content": initial_prompt},
        {"role": "assistant", "content": response},
    ]
    decisions = []
    question_num = 0

    while True:
        question_num += 1

        # Display AI question
        console.print(Panel(
            Markdown(response),
            title=f"{t('prp.validate_question')} #{question_num}",
            border_style="yellow",
        ))

        # Get developer response
        console.print()
        answer = Prompt.ask(
            t("prp.validate_answer_prompt"),
            default=t("prp.validate_done_default"),
        )

        if answer.lower() in ("done", "skip", "pronto", "pular", ""):
            break

        # Record decision
        decisions.append({
            "question_num": question_num,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
        })

        # Continue conversation
        follow_up = (
            f"Developer's answer: {answer}\n\n"
            f"Record this decision and ask the next critical question. "
            f"If all important decisions have been covered, say "
            f"'VALIDATION COMPLETE' and provide a summary."
        )

        messages.append({"role": "user", "content": follow_up})

        try:
            response = ai.run_conversation(messages, system=PRP_VALIDATE_SYSTEM)
        except Exception as e:
            console.print(f"{t('common.error')} {e}")
            break

        messages.append({"role": "assistant", "content": response})

        # Check if AI indicated completion
        if "VALIDATION COMPLETE" in response.upper():
            console.print(Panel(
                Markdown(response),
                title=t("prp.validate_complete_title"),
                border_style="green",
            ))
            break

    # Save validation results
    if decisions:
        _save_validation(prp_path, decisions, ctx)

    console.print(f"\n{t('common.success')} {t('prp.validate_finished', count=len(decisions))}")

    # Ask to approve
    if decisions and Confirm.ask(t("prp.validate_approve_confirm")):
        _approve_prp(prp_path, ctx)
        console.print(f"{t('common.success')} {t('prp.validate_approved')}")
        console.print(t("prp.validate_build_hint", prp_file=str(prp_path)))


def _save_validation(prp_path: Path, decisions: list, ctx):
    """Save validation decisions to a companion file"""
    validation_path = prp_path.with_name(
        prp_path.stem + "-validation.md"
    )

    lines = [
        f"# Validation: {prp_path.stem}\n",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"**Decisions**: {len(decisions)}\n",
        "",
        "## Decisions\n",
    ]

    for d in decisions:
        lines.append(f"### Q{d['question_num']}")
        lines.append(f"**Answer**: {d['answer']}\n")

    validation_path.write_text("\n".join(lines), encoding="utf-8")

    # Update manifest
    if ctx:
        prp_id = prp_path.stem.split("-validation")[0]
        for prp in ctx.manifest.get("prps", []):
            if prp_id.startswith(prp.get("id", "")):
                prp["decisions_count"] = len(decisions)
                prp["status"] = "validated"
                break
        ctx.manifest["last_updated"] = datetime.now().isoformat()
        ctx.save()


def _approve_prp(prp_path: Path, ctx):
    """Mark PRP as approved in manifest"""
    if not ctx:
        return

    prp_stem = prp_path.stem
    now = datetime.now().isoformat()

    for prp in ctx.manifest.get("prps", []):
        if prp_stem.startswith(prp.get("id", "")):
            prp["status"] = "approved"
            prp["approved_at"] = now
            break

    ctx.manifest["last_updated"] = now
    ctx.save()

    ctx.progress.setdefault("recent_activity", []).insert(0, {
        "date": now,
        "action": f"PRP {prp_stem} approved",
    })
    ctx.save()


# ---------------------------------------------------------------------------
# execute
# ---------------------------------------------------------------------------

def execute_prp(prp_file: Optional[str]):
    """Execute an approved PRP by delegating to build command"""
    if not prp_file:
        console.print(f"{t('common.error')} {t('prp.specify_prp')}")
        return

    prp_path = Path(prp_file)
    if not prp_path.exists():
        console.print(f"{t('common.error')} {t('prp.file_not_found', file=prp_file)}")
        return

    # Check approval status
    ctx = get_project_context()
    if ctx:
        prp_stem = prp_path.stem
        for prp in ctx.manifest.get("prps", []):
            if prp_stem.startswith(prp.get("id", "")):
                if prp.get("status") not in ("approved", "validated", "in_progress"):
                    console.print(
                        f"{t('common.warning')} "
                        f"{t('prp.execute_not_approved', file=prp_file)}"
                    )
                    if not Confirm.ask(t("prp.execute_anyway_confirm")):
                        return
                break

    console.print(t("prp.execute_delegating"))

    # Delegate to build
    backend = get_ai_backend()
    if backend == AIBackend.OFFLINE:
        console.print(f"{t('common.error')} {t('prp.ai_required')}")
        return

    from codrsync.ai import build as build_module
    build_module.run(backend=backend, prp=str(prp_path))
