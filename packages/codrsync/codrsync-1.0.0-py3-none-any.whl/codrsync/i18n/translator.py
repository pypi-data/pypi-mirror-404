"""
Translation via Anthropic API for non-built-in languages.

Translates EN strings to the target language, preserving:
- Rich markup ([bold], [red], etc.)
- Placeholders ({var})
- Command names (codrsync, PRP, etc.)

Results are cached automatically.
"""

import json
import os

from codrsync.i18n.strings import EN
from codrsync.i18n.loader import save_to_cache


def translate_via_api(target_lang: str, api_key: str | None = None) -> dict[str, str] | None:
    """Translate all EN strings to target_lang using Anthropic API.

    Returns the translated dict, or None if translation fails.
    Saves to cache on success.
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    # Build the prompt with all EN strings
    source_json = json.dumps(EN, indent=2, ensure_ascii=False)

    prompt = f"""Translate the following JSON dictionary of UI strings from English to {target_lang}.

RULES:
1. Preserve ALL Rich markup tags exactly: [bold], [red], [green], [yellow], [cyan], [dim], [/bold], [/red], etc.
2. Preserve ALL placeholders exactly: {{version}}, {{name}}, {{number}}, {{count}}, {{points}}, etc.
3. Preserve ALL command names exactly: codrsync, PRP, INITIAL.md, Claude Code, ANTHROPIC_API_KEY
4. Preserve ALL technical terms: JSON, CSV, Excel, Jira, Trello, Notion, Mermaid, API, CLI, backend, frontend
5. Keep the same JSON keys (do NOT translate keys, only values)
6. Return ONLY valid JSON, no explanations

Source strings:
```json
{source_json}
```

Return the translated JSON:"""

    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                if line.strip() == "```" and in_block:
                    break
                if in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        translations = json.loads(text)

        # Validate it has strings (not necessarily all keys on first pass)
        if isinstance(translations, dict) and len(translations) > 0:
            # Fill in any missing keys with EN defaults
            for key in EN:
                if key not in translations:
                    translations[key] = EN[key]

            save_to_cache(target_lang.lower(), translations)
            return translations

    except Exception:
        pass

    return None
