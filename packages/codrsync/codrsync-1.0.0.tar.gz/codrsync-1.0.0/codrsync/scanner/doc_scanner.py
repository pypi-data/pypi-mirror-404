"""
Scan documentation files: README, CLAUDE.md, docs/ directory.
"""

from dataclasses import dataclass, field
from pathlib import Path


DOC_FILES = [
    "README.md",
    "README.rst",
    "README.txt",
    "README",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "ARCHITECTURE.md",
    "docs/",
]


@dataclass
class DocScanResult:
    """Result of documentation scanning."""

    found_files: list[str] = field(default_factory=list)
    readme_content: str = ""
    claude_md_content: str = ""
    docs_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "found_files": self.found_files,
            "has_readme": bool(self.readme_content),
            "has_claude_md": bool(self.claude_md_content),
            "docs_count": len(self.docs_files),
            "docs_files": self.docs_files,
        }


def scan_docs(path: Path) -> DocScanResult:
    """Scan for documentation files and read their contents."""
    result = DocScanResult()

    for doc in DOC_FILES:
        target = path / doc
        if target.exists():
            result.found_files.append(doc)

    # Read README
    for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
        readme_path = path / readme_name
        if readme_path.is_file():
            try:
                result.readme_content = readme_path.read_text(errors="replace")[:5000]
            except OSError:
                pass
            break

    # Read CLAUDE.md
    claude_path = path / "CLAUDE.md"
    if claude_path.is_file():
        try:
            result.claude_md_content = claude_path.read_text(errors="replace")[:5000]
        except OSError:
            pass

    # List docs/ contents
    docs_dir = path / "docs"
    if docs_dir.is_dir():
        try:
            for f in sorted(docs_dir.rglob("*")):
                if f.is_file():
                    rel = str(f.relative_to(path))
                    result.docs_files.append(rel)
        except OSError:
            pass

    return result
