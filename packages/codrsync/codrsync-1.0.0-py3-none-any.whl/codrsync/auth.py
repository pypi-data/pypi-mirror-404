"""
Authentication and AI backend detection
"""

import os
import shutil
from enum import Enum
from typing import Optional

from rich.console import Console
from rich.panel import Panel
import questionary

from codrsync.config import get_config, Config


console = Console()


class AIBackend(Enum):
    CLAUDE_CODE = "claude-code"
    ANTHROPIC_API = "anthropic-api"
    OFFLINE = "offline"


def detect_claude_code() -> bool:
    """Check if Claude Code CLI is installed"""
    return shutil.which("claude") is not None


def detect_anthropic_api() -> bool:
    """Check if Anthropic API key is configured"""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def get_ai_backend() -> AIBackend:
    """
    Detect which AI backend to use.

    Priority:
    1. Explicit config setting
    2. Claude Code (if installed)
    3. Anthropic API (if key present)
    4. Offline mode
    """
    from codrsync.i18n import t

    config = get_config()

    # Check explicit config
    if config.ai_backend == "claude-code":
        if detect_claude_code():
            return AIBackend.CLAUDE_CODE
        console.print(f"{t('common.warning')} {t('auth.warning_claude_fallback')}")

    if config.ai_backend == "anthropic-api":
        if detect_anthropic_api() or config.anthropic_api_key:
            return AIBackend.ANTHROPIC_API
        console.print(f"{t('common.warning')} {t('auth.warning_api_fallback')}")

    if config.ai_backend == "offline":
        return AIBackend.OFFLINE

    # Auto-detect
    if detect_claude_code():
        return AIBackend.CLAUDE_CODE

    if detect_anthropic_api():
        return AIBackend.ANTHROPIC_API

    return AIBackend.OFFLINE


def show_auth_status():
    """Show current authentication status"""
    from codrsync.i18n import t

    backend = get_ai_backend()
    config = get_config()

    claude_installed = t("auth.installed") if detect_claude_code() else t("auth.not_found")
    claude_icon = "[green]✓[/green]" if detect_claude_code() else "[red]✗[/red]"
    api_configured = t("auth.configured") if detect_anthropic_api() else t("auth.not_set")
    api_icon = "[green]✓[/green]" if detect_anthropic_api() else "[red]✗[/red]"

    status_text = f"""
{t('auth.current_backend')} {backend.value}

{t('auth.available_backends')}
  {t('auth.claude_code_label')}    {claude_icon} {claude_installed}
  {t('auth.anthropic_api_label')}  {api_icon} {api_configured}

{t('auth.config_label')}
  ai_backend: {config.ai_backend}
  auto_research: {config.auto_research}
  explanation_level: {config.explanation_level}
"""

    console.print(Panel(status_text, title=t("auth.status_title"), border_style="blue"))


def configure_auth():
    """Interactive authentication configuration"""
    from codrsync.i18n import t

    console.print(f"\n{t('auth.setup_title')}\n")

    # Detect available options
    has_claude_code = detect_claude_code()
    has_api_key = detect_anthropic_api()

    choices = []

    if has_claude_code:
        choices.append({
            "name": t("auth.claude_detected"),
            "value": "claude-code"
        })
    else:
        choices.append({
            "name": t("auth.claude_not_installed"),
            "value": "claude-code",
            "disabled": t("auth.claude_install_hint")
        })

    choices.append({
        "name": t("auth.api_detected") if has_api_key else t("auth.api_enter"),
        "value": "anthropic-api"
    })

    choices.append({
        "name": t("auth.offline_option"),
        "value": "offline"
    })

    selected = questionary.select(
        t("auth.backend_question"),
        choices=choices,
    ).ask()

    if selected is None:
        raise SystemExit(0)

    config = get_config()
    config.ai_backend = selected

    if selected == "anthropic-api" and not has_api_key:
        api_key = questionary.password(
            t("auth.enter_api_key")
        ).ask()

        if api_key:
            config.anthropic_api_key = api_key
            console.print(f"\n{t('common.success')} {t('auth.api_key_saved')}")
            console.print(f"{t('common.tip')} {t('auth.api_key_tip')}")

    config.save()

    console.print(f"\n{t('common.success')} {t('auth.config_saved')}")
    console.print(f"  {t('auth.backend_label')} [bold]{selected}[/bold]")

    if selected == "offline":
        console.print(f"\n{t('common.note')} {t('auth.offline_note')}")
        console.print(t("auth.offline_commands"))
