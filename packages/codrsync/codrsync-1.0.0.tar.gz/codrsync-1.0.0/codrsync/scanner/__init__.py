"""
Scanner package - detect project stack, docs, and GitHub info.
"""

from codrsync.scanner.detector import detect, has_existing_code, DetectionResult
from codrsync.scanner.doc_scanner import scan_docs, DocScanResult
from codrsync.scanner.github_scanner import scan_github, GitHubScanResult
from codrsync.scanner.context_generator import generate_context
from codrsync.scanner.scan import run

__all__ = [
    "detect",
    "has_existing_code",
    "DetectionResult",
    "scan_docs",
    "DocScanResult",
    "scan_github",
    "GitHubScanResult",
    "generate_context",
    "run",
]
