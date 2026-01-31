"""
Scan GitHub repository info via `gh` CLI.
"""

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class GitHubScanResult:
    """Result of GitHub scanning."""

    available: bool = False
    is_repo: bool = False
    repo_name: str = ""
    issues: list[dict] = field(default_factory=list)
    pull_requests: list[dict] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "is_repo": self.is_repo,
            "repo_name": self.repo_name,
            "open_issues": len(self.issues),
            "open_prs": len(self.pull_requests),
            "workflows": self.workflows,
            "issues": self.issues[:20],
            "pull_requests": self.pull_requests[:20],
        }


def _run_gh(args: list[str], cwd: Path, timeout: int = 30) -> Optional[str]:
    """Run a gh CLI command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def scan_github(path: Path) -> GitHubScanResult:
    """Scan GitHub repository information using the gh CLI."""
    result = GitHubScanResult()

    # Check if gh CLI is available
    if not shutil.which("gh"):
        result.error = "gh_not_available"
        return result
    result.available = True

    # Check if this is a git repo with a remote
    repo_name = _run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd=path)
    if not repo_name:
        result.error = "not_a_repo"
        return result

    result.is_repo = True
    result.repo_name = repo_name

    # Fetch open issues
    issues_json = _run_gh(
        ["issue", "list", "--state", "open", "--limit", "20", "--json", "number,title,labels,assignees"],
        cwd=path,
    )
    if issues_json:
        try:
            result.issues = json.loads(issues_json)
        except json.JSONDecodeError:
            pass

    # Fetch open PRs
    prs_json = _run_gh(
        ["pr", "list", "--state", "open", "--limit", "20", "--json", "number,title,headRefName,author"],
        cwd=path,
    )
    if prs_json:
        try:
            result.pull_requests = json.loads(prs_json)
        except json.JSONDecodeError:
            pass

    # List GitHub Actions workflows
    workflows_dir = path / ".github" / "workflows"
    if workflows_dir.is_dir():
        result.workflows = [f.name for f in sorted(workflows_dir.iterdir()) if f.suffix in (".yml", ".yaml")]

    return result
