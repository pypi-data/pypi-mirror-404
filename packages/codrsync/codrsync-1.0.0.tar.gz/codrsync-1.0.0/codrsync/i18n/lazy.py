"""
LazyString - Deferred translation resolution for Typer help strings.

Typer evaluates help= strings at import-time, before the user's language
preference is known. LazyString resolves the translation eagerly at creation
time (using the configured language from config.json) and stores it as the
base str value. This ensures C-level str operations (regex, Rich markup
parsing, etc.) work correctly.

We inherit from str so that isinstance(lazy, str) returns True,
which is required by Rich's Panel and Click/Typer internals.
"""

from __future__ import annotations


class LazyString(str):
    """A str subclass that resolves its translation at creation time.

    The base str is initialized with the resolved translation, ensuring
    C-level str operations work correctly with the actual text.
    """

    def __new__(cls, key: str, **kwargs):
        from codrsync.i18n import resolve
        text = resolve(key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        instance = super().__new__(cls, text)
        instance._key = key
        instance._kwargs = kwargs
        return instance

    def __repr__(self) -> str:
        return f"LazyString({self._key!r})"
