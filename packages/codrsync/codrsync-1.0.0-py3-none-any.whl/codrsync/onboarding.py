"""
First-run onboarding experience for codrsync.

Detects first execution (no config.json), shows welcome panel,
language selection, tour, and next steps.
"""

import os

from rich.console import Console
from rich.panel import Panel
import questionary

from codrsync.config import Config, CODRSYNC_HOME
from codrsync.i18n import setup_language, t
from codrsync.i18n.strings import EN


console = Console()

# Language choices for the onboarding prompt.
# Welcome panel is always in English since no language is selected yet.
LANGUAGE_CHOICES = [
    {"name": "English", "value": "en"},
    {"name": "Portugues (Brasil)", "value": "pt-br"},
    {"name": "Espanol", "value": "es"},
    {"name": "Francais", "value": "fr"},
    {"name": "Deutsch", "value": "de"},
    {"name": "Italiano", "value": "it"},
    {"name": "Other (type language code)", "value": "__other__"},
]


def run_onboarding() -> None:
    """Run the first-run onboarding experience."""
    import sys

    # Welcome panel (always in English - no language chosen yet)
    console.print()
    console.print(Panel(
        "[bold cyan]codrsync[/bold cyan] - Turn any dev into jedi ninja codr\n\n"
        "AI-powered development orchestrator with guided development,\n"
        "interactive validation, and persistent context.",
        title="Welcome to codrsync!",
        border_style="cyan",
    ))
    console.print()

    # Non-interactive mode: default to English
    if not sys.stdin.isatty():
        lang = "en"
    else:
        # Language selection
        lang = questionary.select(
            "Choose your language:",
            choices=LANGUAGE_CHOICES,
        ).ask()

        if lang is None:
            # User cancelled
            lang = "en"

        if lang == "__other__":
            lang = questionary.text(
                "Enter language code (e.g. ja, ko, zh):"
            ).ask()
            if not lang:
                lang = "en"
            lang = lang.strip().lower()

    # For non-built-in languages, try API translation
    from codrsync.i18n.strings import BUILTIN_LANGUAGES
    if lang not in BUILTIN_LANGUAGES:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # Check if config has one
            try:
                cfg = Config.load()
                api_key = cfg.anthropic_api_key
            except Exception:
                pass

        if not api_key:
            console.print(Panel(
                f"Language '{lang}' requires translation via Anthropic API.\n"
                "No API key configured. Falling back to English.\n\n"
                "Run [bold]codrsync auth[/bold] to configure an API key.",
                border_style="yellow",
            ))
            lang = "en"
        else:
            console.print(f"  Translating to {lang}...")
            from codrsync.i18n.translator import translate_via_api
            result = translate_via_api(lang, api_key)
            if result is None:
                console.print("  Translation failed. Using English.")
                lang = "en"

    # Activate language
    setup_language(lang)

    # Save config with language preference
    CODRSYNC_HOME.mkdir(parents=True, exist_ok=True)
    config = Config(language=lang)
    config.save()

    # Tour (now in the selected language)
    console.print()
    console.print(Panel(
        t("onboarding.tour_body"),
        title=t("onboarding.tour_title"),
        border_style="blue",
    ))

    # Next steps
    console.print()
    console.print(Panel(
        t("onboarding.ready_body"),
        title=t("onboarding.ready_title"),
        border_style="green",
    ))
    console.print()
