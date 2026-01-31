"""
Contextual next-step suggestions for codrsync.

Detects current state and suggests the most useful next action.
"""

from rich.console import Console

from codrsync.i18n import t
from codrsync.config import CODRSYNC_CONFIG, get_project_context


console = Console()


def suggest_next_steps() -> None:
    """Detect state and suggest the next action."""
    # No config -> auth
    if not CODRSYNC_CONFIG.exists():
        console.print(f"\n  {t('next.suggestion_title')} {t('next.no_config')}")
        return

    # No project in current dir -> init
    ctx = get_project_context()
    if ctx is None:
        console.print(f"\n  {t('next.suggestion_title')} {t('next.no_project')}")
        return

    # Has project but no sprint -> sprint start
    sprint = ctx.manifest.get("current_sprint")
    if not sprint:
        console.print(f"\n  {t('next.suggestion_title')} {t('next.no_sprint')}")
        return
