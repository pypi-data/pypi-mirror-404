"""
/codrsync init - Project kickstart wizard

Uses AI to guide project creation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import questionary

from codrsync.auth import AIBackend
from codrsync.ai.backend import get_backend_instance
from codrsync.config import get_config
from codrsync.i18n import t


console = Console()


# Kickstart prompt template
KICKSTART_PROMPT = """
You are codrsync, an AI development orchestrator. You're helping a developer start a new project.

Developer info:
- Name: {dev_name}
- Level: {dev_level}

Project info:
- Name: {project_name}
- Description: {project_description}
- Type: {project_type}

Your task: Generate the initial project structure files.

Please provide:
1. A recommended tech stack (if not specified)
2. The manifest.json content
3. The progress.json content
4. A list of recommended PRPs for the MVP
5. The first PRP outline

Respond in JSON format with these keys:
- tech_stack: object with frontend, backend, database, extras
- manifest: full manifest.json content
- progress: full progress.json content
- prps: array of {id, name, description}
- first_prp: outline of PRP-01
"""


def run(
    backend: AIBackend,
    name: Optional[str] = None,
    skip_research: bool = False
):
    """Run the kickstart wizard"""
    console.print(Panel(
        f"{t('kickstart.wizard_title')}\n\n"
        f"{t('kickstart.wizard_intro')}",
        border_style="cyan"
    ))

    # Check if project already exists
    if Path("doc/project/manifest.json").exists():
        console.print(t("kickstart.project_exists"))
        if not Confirm.ask(t("kickstart.overwrite_confirm")):
            return

    # Phase 1: Know the developer
    console.print(f"\n{t('kickstart.phase1')}\n")

    dev_name = Prompt.ask(t("kickstart.ask_name"))

    dev_level = questionary.select(
        t("kickstart.ask_level"),
        choices=[
            {"name": t("kickstart.level_beginner"), "value": "beginner"},
            {"name": t("kickstart.level_intermediate"), "value": "intermediate"},
            {"name": t("kickstart.level_advanced"), "value": "advanced"},
        ]
    ).ask()

    console.print(f"\n{t('kickstart.greeting', name=dev_name)}\n")

    # Phase 2: Understand the project
    console.print(f"{t('kickstart.phase2')}\n")

    if not name:
        project_name = Prompt.ask(t("kickstart.ask_project_name"))
    else:
        project_name = name

    project_description = Prompt.ask(
        t("kickstart.ask_description"),
        default=t("kickstart.default_description")
    )

    project_type = questionary.select(
        t("kickstart.ask_type"),
        choices=[
            {"name": t("kickstart.type_webapp"), "value": "webapp"},
            {"name": t("kickstart.type_api"), "value": "api"},
            {"name": t("kickstart.type_saas"), "value": "saas"},
            {"name": t("kickstart.type_mobile"), "value": "mobile"},
            {"name": t("kickstart.type_bot"), "value": "bot"},
            {"name": t("kickstart.type_cli"), "value": "cli"},
        ]
    ).ask()

    # Phase 3: Tech decisions
    console.print(f"\n{t('kickstart.phase3')}\n")

    tech_choice = questionary.select(
        t("kickstart.ask_tech_choice"),
        choices=[
            {"name": t("kickstart.tech_manual"), "value": "manual"},
            {"name": t("kickstart.tech_research"), "value": "research"},
        ]
    ).ask()

    tech_stack = None

    if tech_choice == "manual":
        tech_stack = {
            "frontend": Prompt.ask(t("kickstart.frontend_prompt"), default="None"),
            "backend": Prompt.ask(t("kickstart.backend_prompt"), default="Python + FastAPI"),
            "database": Prompt.ask(t("kickstart.database_prompt"), default="PostgreSQL"),
            "extras": Prompt.ask(t("kickstart.extras_prompt"), default="").split(",")
        }
    else:
        console.print(f"\n{t('kickstart.researching')}\n")

        if not skip_research:
            # Use AI to research
            ai = get_backend_instance(backend)
            research_prompt = f"""
            Research the best tech stack for a {project_type} project in 2026.
            The project is: {project_description}

            Provide a JSON response with:
            - frontend: recommended frontend tech
            - backend: recommended backend tech
            - database: recommended database
            - extras: array of additional tools
            - reasoning: brief explanation
            """

            try:
                response = ai.run_prompt(research_prompt)
                console.print(f"[dim]{t('kickstart.research_complete')}[/dim]")
            except Exception as e:
                console.print(f"[yellow]{t('kickstart.research_failed', error=e)}[/yellow]")

        # Default recommendations based on project type
        defaults = {
            "webapp": {"frontend": "Next.js", "backend": "Python + FastAPI", "database": "PostgreSQL"},
            "api": {"frontend": "None", "backend": "Python + FastAPI", "database": "PostgreSQL"},
            "saas": {"frontend": "Next.js", "backend": "Python + FastAPI", "database": "PostgreSQL"},
            "mobile": {"frontend": "React Native", "backend": "Python + FastAPI", "database": "PostgreSQL"},
            "bot": {"frontend": "None", "backend": "Python", "database": "SQLite"},
            "cli": {"frontend": "None", "backend": "Python + Typer", "database": "SQLite"},
        }

        tech_stack = defaults.get(project_type, defaults["webapp"])
        tech_stack["extras"] = ["Docker", "Redis"]

        console.print(Panel(
            f"{t('kickstart.recommended_stack')}\n\n"
            f"  {t('kickstart.frontend_label')} {tech_stack['frontend']}\n"
            f"  {t('kickstart.backend_label')} {tech_stack['backend']}\n"
            f"  {t('kickstart.database_label')} {tech_stack['database']}\n"
            f"  {t('kickstart.extras_label')} {', '.join(tech_stack.get('extras', []))}",
            title=t("kickstart.tech_stack_title"),
            border_style="green"
        ))

        if not Confirm.ask(t("kickstart.use_stack_confirm")):
            # Let them customize
            tech_stack["frontend"] = Prompt.ask(t("kickstart.frontend_prompt"), default=tech_stack["frontend"])
            tech_stack["backend"] = Prompt.ask(t("kickstart.backend_prompt"), default=tech_stack["backend"])
            tech_stack["database"] = Prompt.ask(t("kickstart.database_prompt"), default=tech_stack["database"])

    # Phase 4: Create project
    console.print(f"\n{t('kickstart.phase4')}\n")

    if not Confirm.ask(t("kickstart.create_confirm", name=project_name)):
        console.print(t("common.cancelled"))
        return

    # Create directory structure
    create_project_structure(
        project_name=project_name,
        project_description=project_description,
        project_type=project_type,
        tech_stack=tech_stack,
        dev_name=dev_name,
        dev_level=dev_level
    )

    # Done!
    console.print(Panel(
        f"{t('kickstart.success')}\n\n"
        f"{project_name}\n\n"
        f"{t('kickstart.next_steps')}\n"
        f"  {t('kickstart.next_step_1')}\n"
        f"  {t('kickstart.next_step_2')}\n"
        f"  {t('kickstart.next_step_3')}\n",
        title=t("kickstart.success_title"),
        border_style="green"
    ))


def create_project_structure(
    project_name: str,
    project_description: str,
    project_type: str,
    tech_stack: dict,
    dev_name: str,
    dev_level: str
):
    """Create all project files"""
    slug = project_name.lower().replace(" ", "-")
    now = datetime.now().isoformat()

    # Create directories
    dirs = [
        "doc/project",
        "doc/task",
        "PRPs/templates",
        "src",
        "tests",
        "docs",
        "exports",
        ".claude/commands"
    ]

    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Create manifest.json
    manifest = {
        "version": "1.0",
        "project": {
            "name": project_name,
            "slug": slug,
            "description": project_description,
            "type": project_type,
            "created_at": now,
            "phase": "discovery",
            "tech_stack": tech_stack
        },
        "developer": {
            "name": dev_name,
            "level": dev_level,
            "preferences": {
                "explanation_level": "balanced" if dev_level == "intermediate" else (
                    "detailed" if dev_level == "beginner" else "concise"
                ),
                "emojis": False,
                "auto_research": True
            }
        },
        "prps": [],
        "current_sprint": None,
        "milestones": [
            {"id": "M1", "name": "Project Setup", "date": datetime.now().strftime("%Y-%m-%d"), "status": "done"},
            {"id": "M2", "name": "MVP Complete", "date": "", "status": "pending"},
        ],
        "created_by": "codrsync",
        "last_updated": now
    }

    with open("doc/project/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Create progress.json
    progress = {
        "version": "1.0",
        "overall_progress": 5,
        "phases": {
            "discovery": {"status": "done", "progress": 100},
            "design": {"status": "pending", "progress": 0},
            "development": {"status": "pending", "progress": 0},
            "testing": {"status": "pending", "progress": 0},
            "deploy": {"status": "pending", "progress": 0},
            "launch": {"status": "pending", "progress": 0}
        },
        "epics": [],
        "stories": [],
        "blockers": [],
        "recent_activity": [
            {"date": now, "action": f"Project '{project_name}' created with codrsync"}
        ],
        "metrics": {
            "velocity_history": [],
            "average_velocity": 0,
            "total_points_delivered": 0,
            "total_sprints_completed": 0
        },
        "last_updated": now
    }

    with open("doc/project/progress.json", "w") as f:
        json.dump(progress, f, indent=2)

    # Create context-session.md
    with open("doc/task/context-session.md", "w") as f:
        f.write(f"# {project_name} - Context Session\n\n")
        f.write(f"**Created**: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"**Status**: Project initialized\n\n")
        f.write("## Current Focus\n\n")
        f.write("Project setup complete. Ready for first PRP.\n")

    # Create .gitignore
    with open(".gitignore", "w") as f:
        f.write("# Python\n__pycache__/\n*.py[cod]\n.venv/\nvenv/\n")
        f.write("\n# Environment\n.env\n.env.local\n")
        f.write("\n# IDE\n.idea/\n.vscode/\n")
        f.write("\n# OS\n.DS_Store\n")
        f.write("\n# Exports\nexports/\n")

    console.print(f"  {t('common.success')} {t('kickstart.created_structure')}")
    console.print(f"  {t('common.success')} {t('kickstart.created_manifest')}")
    console.print(f"  {t('common.success')} {t('kickstart.created_progress')}")
    console.print(f"  {t('common.success')} {t('kickstart.created_context')}")


def run_from_scan(backend: AIBackend, scan_result: dict):
    """Import an existing project using scan results.

    Creates project structure (manifest, progress) from detected stack
    instead of running the full interactive wizard.
    """
    from codrsync.scanner.detector import DetectionResult

    console.print(f"\n{t('init.importing')}\n")

    # Extract info from scan result
    detection = scan_result.get("detection", {})
    languages = detection.get("languages", [])
    frameworks = detection.get("frameworks", [])
    databases = detection.get("databases", [])

    # Infer tech stack from scan
    tech_stack = {
        "frontend": ", ".join(frameworks) if frameworks else "None",
        "backend": ", ".join(languages) if languages else "Unknown",
        "database": ", ".join(databases) if databases else "None",
        "extras": detection.get("infrastructure", []) + detection.get("tools", []),
    }

    # Ask minimal info
    dev_name = Prompt.ask(t("kickstart.ask_name"))

    dev_level = questionary.select(
        t("kickstart.ask_level"),
        choices=[
            {"name": t("kickstart.level_beginner"), "value": "beginner"},
            {"name": t("kickstart.level_intermediate"), "value": "intermediate"},
            {"name": t("kickstart.level_advanced"), "value": "advanced"},
        ]
    ).ask()

    # Infer project name from directory or package.json
    project_path = Path(scan_result.get("path", "."))
    project_name = project_path.name

    # Try to get name from package.json or pyproject.toml
    pkg_path = project_path / "package.json"
    if pkg_path.exists():
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            project_name = pkg.get("name", project_name)
        except (json.JSONDecodeError, OSError):
            pass

    project_name = Prompt.ask(t("kickstart.ask_project_name"), default=project_name)
    project_description = Prompt.ask(
        t("kickstart.ask_description"),
        default=t("kickstart.default_description"),
    )

    # Infer project type
    project_type = "webapp"
    if not frameworks or all("None" in f for f in frameworks):
        project_type = "api"
    if any("cli" in l.lower() or "typer" in l.lower() for l in detection.get("tools", [])):
        project_type = "cli"

    # Create project structure
    create_project_structure(
        project_name=project_name,
        project_description=project_description,
        project_type=project_type,
        tech_stack=tech_stack,
        dev_name=dev_name,
        dev_level=dev_level,
    )

    console.print(Panel(
        f"{t('init.import_complete')}\n\n"
        f"{project_name}\n\n"
        f"{t('kickstart.next_steps')}\n"
        f"  {t('kickstart.next_step_1')}\n"
        f"  {t('kickstart.next_step_2')}\n"
        f"  {t('kickstart.next_step_3')}\n",
        title=t("kickstart.success_title"),
        border_style="green",
    ))
