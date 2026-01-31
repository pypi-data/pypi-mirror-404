"""
Generate AI-powered project context document from scan results.
"""

from pathlib import Path
from typing import Optional

from codrsync.scanner.detector import DetectionResult
from codrsync.scanner.doc_scanner import DocScanResult
from codrsync.scanner.github_scanner import GitHubScanResult


CONTEXT_PROMPT = """\
You are codrsync, an AI development orchestrator. Analyze the following project scan results and generate a concise project context document in Markdown.

## Detected Stack
{stack_section}

## Documentation
{docs_section}

## GitHub
{github_section}

---

Generate a Markdown document with these sections:
1. **Project Overview** - infer from the stack and docs what this project does
2. **Tech Stack Summary** - organized list of detected technologies
3. **Architecture Notes** - infer architecture from the stack (monorepo? microservices? monolith?)
4. **Key Files** - important config files and entry points
5. **Development Notes** - build/test/deploy patterns detected
6. **Open Work** - summarize open issues/PRs if available

Keep it concise and actionable. Write in English.
"""


def _build_stack_section(detection: DetectionResult) -> str:
    lines = []
    for label, items in [
        ("Languages", detection.languages),
        ("Frameworks", detection.frameworks),
        ("Databases", detection.databases),
        ("Infrastructure", detection.infrastructure),
        ("Tools", detection.tools),
    ]:
        if items:
            lines.append(f"- **{label}**: {', '.join(items)}")
    return "\n".join(lines) if lines else "No stack detected."


def _build_docs_section(docs: Optional[DocScanResult]) -> str:
    if not docs or not docs.found_files:
        return "No documentation files found."
    lines = [f"- Found: {', '.join(docs.found_files)}"]
    if docs.readme_content:
        preview = docs.readme_content[:500].replace("\n", "\n> ")
        lines.append(f"\nREADME preview:\n> {preview}")
    return "\n".join(lines)


def _build_github_section(github: Optional[GitHubScanResult]) -> str:
    if not github or not github.is_repo:
        return "Not a GitHub repository or gh CLI not available."
    lines = [f"- Repository: {github.repo_name}"]
    lines.append(f"- Open issues: {len(github.issues)}")
    lines.append(f"- Open PRs: {len(github.pull_requests)}")
    if github.workflows:
        lines.append(f"- Workflows: {', '.join(github.workflows)}")
    if github.issues:
        lines.append("\nTop issues:")
        for issue in github.issues[:5]:
            lines.append(f"  - #{issue.get('number', '?')}: {issue.get('title', 'Untitled')}")
    return "\n".join(lines)


def build_prompt(
    detection: DetectionResult,
    docs: Optional[DocScanResult] = None,
    github: Optional[GitHubScanResult] = None,
) -> str:
    """Build the AI prompt from scan results."""
    return CONTEXT_PROMPT.format(
        stack_section=_build_stack_section(detection),
        docs_section=_build_docs_section(docs),
        github_section=_build_github_section(github),
    )


def generate_context(
    project_path: Path,
    detection: DetectionResult,
    docs: Optional[DocScanResult] = None,
    github: Optional[GitHubScanResult] = None,
    backend=None,
) -> Optional[str]:
    """Generate context document using AI and save to doc/project/context.md.

    Returns the path to the saved file, or None on failure.
    """
    if backend is None:
        return None

    prompt = build_prompt(detection, docs, github)

    try:
        content = backend.run_prompt(prompt)
    except Exception:
        return None

    output_dir = project_path / "doc" / "project"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "context.md"
    output_path.write_text(content)

    return str(output_path)
