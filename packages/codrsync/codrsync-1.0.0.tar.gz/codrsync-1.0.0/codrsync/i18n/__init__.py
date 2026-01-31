"""
codrsync i18n - Internationalization support.

Public API:
    t(key, **kwargs)        -> str          Immediate translation
    lazy_t(key, **kwargs)   -> LazyString   Deferred translation (for Typer help=)
    setup_language(code)    -> None         Set active language
    resolve(key)            -> str          Resolve key to translated string
"""

from codrsync.i18n.lazy import LazyString
from codrsync.i18n.strings import EN, BUILTIN_LANGUAGES

# Module-level state
_current_language: str | None = None
_translations: dict[str, str] | None = None
_initialized: bool = False


def _ensure_initialized() -> None:
    """Auto-initialize from config if not yet done."""
    global _current_language, _translations, _initialized

    if _initialized:
        return

    _initialized = True

    # Read language from config
    try:
        from codrsync.config import CODRSYNC_CONFIG
        if CODRSYNC_CONFIG.exists():
            import json
            with open(CODRSYNC_CONFIG) as f:
                data = json.load(f)
            lang = data.get("language", "en")
        else:
            lang = "en"
    except Exception:
        lang = "en"

    _current_language = lang.lower()

    # Load translations
    from codrsync.i18n.loader import load_language
    _translations = load_language(_current_language)

    # Fallback to EN
    if _translations is None:
        _translations = EN


def setup_language(lang_code: str) -> None:
    """Set the active language. Call before any t()/lazy_t() usage."""
    global _current_language, _translations, _initialized

    _current_language = lang_code.lower()
    _initialized = True

    from codrsync.i18n.loader import load_language
    _translations = load_language(_current_language)

    if _translations is None:
        _translations = EN


def resolve(key: str) -> str:
    """Resolve a translation key to a string.

    Called by LazyString.__str__() and t().
    """
    _ensure_initialized()

    if _translations and key in _translations:
        return _translations[key]

    # Fallback to EN
    return EN.get(key, key)


def t(key: str, **kwargs) -> str:
    """Translate a key immediately.

    Use for runtime strings (console.print, prompts, etc.)
    """
    text = resolve(key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def lazy_t(key: str, **kwargs) -> LazyString:
    """Create a lazy translation.

    Use for import-time strings (Typer help=, rich_help_panel=).
    Resolution is deferred until __str__() is called.
    """
    return LazyString(key, **kwargs)


__all__ = ["t", "lazy_t", "setup_language", "resolve"]
