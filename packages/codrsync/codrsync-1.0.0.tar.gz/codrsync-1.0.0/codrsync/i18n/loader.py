"""
Language loading and caching for codrsync i18n.

Resolution order: built-in dict -> cache file -> None
Cache location: ~/.codrsync/i18n/{lang}.json
"""

import json
from pathlib import Path

from codrsync.config import CODRSYNC_HOME
from codrsync.i18n.strings import BUILTIN_LANGUAGES, KEYS


_I18N_CACHE_DIR = CODRSYNC_HOME / "i18n"


def load_language(lang_code: str) -> dict[str, str] | None:
    """Load translations for a language.

    Resolution: built-in -> cache file -> None
    """
    lang_code = lang_code.lower()

    # 1. Built-in
    if lang_code in BUILTIN_LANGUAGES:
        return BUILTIN_LANGUAGES[lang_code]

    # 2. Cache file
    cache_path = _I18N_CACHE_DIR / f"{lang_code}.json"
    if cache_path.exists():
        try:
            with open(cache_path) as f:
                translations = json.load(f)
            if _is_complete(translations):
                return translations
        except (json.JSONDecodeError, OSError):
            pass

    return None


def save_to_cache(lang_code: str, translations: dict[str, str]) -> None:
    """Save translations to cache file."""
    _I18N_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _I18N_CACHE_DIR / f"{lang_code.lower()}.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(translations, f, indent=2, ensure_ascii=False)


def _is_complete(translations: dict[str, str]) -> bool:
    """Check if translations contain all required keys."""
    return all(key in translations for key in KEYS)
