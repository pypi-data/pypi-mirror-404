"""
AI Backend abstraction - supports Claude Code CLI or Anthropic API
"""

import os
import subprocess
import json
from abc import ABC, abstractmethod
from typing import Optional, Generator
from pathlib import Path

from rich.console import Console

from codrsync.auth import AIBackend


console = Console()


class AIBackendBase(ABC):
    """Abstract base for AI backends"""

    @abstractmethod
    def run_prompt(
        self,
        prompt: str,
        context: Optional[dict] = None,
        system: Optional[str] = None,
    ) -> str:
        """Run a prompt and return the response"""
        pass

    @abstractmethod
    def run_interactive(
        self,
        prompt: str,
        context: Optional[dict] = None,
        system: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Run an interactive session, yielding responses"""
        pass

    def run_conversation(
        self,
        messages: list[dict],
        system: Optional[str] = None,
    ) -> str:
        """Run a multi-turn conversation. Default: use last user message as prompt."""
        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user = msg["content"]
                break
        return self.run_prompt(last_user, system=system)


class ClaudeCodeBackend(AIBackendBase):
    """Uses Claude Code CLI"""

    def __init__(self):
        self.claude_path = "claude"

    def run_prompt(
        self,
        prompt: str,
        context: Optional[dict] = None,
        system: Optional[str] = None,
    ) -> str:
        """Run prompt via Claude Code CLI"""
        full_prompt = self._build_prompt(prompt, context, system)
        cmd = [self.claude_path, "-p", full_prompt]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    def run_interactive(
        self,
        prompt: str,
        context: Optional[dict] = None,
        system: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Run interactive Claude Code session"""
        yield self.run_prompt(prompt, context, system)

    def run_conversation(
        self,
        messages: list[dict],
        system: Optional[str] = None,
    ) -> str:
        """Run conversation via Claude Code CLI using --continue flag"""
        # Claude Code CLI doesn't support multi-turn natively via -p,
        # so we concatenate the conversation into a single prompt.
        parts = []
        if system:
            parts.append(f"<system>\n{system}\n</system>\n")

        for msg in messages:
            role = msg["role"].upper()
            parts.append(f"[{role}]\n{msg['content']}\n")

        full_prompt = "\n".join(parts)
        cmd = [self.claude_path, "-p", full_prompt]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def _build_prompt(
        prompt: str,
        context: Optional[dict] = None,
        system: Optional[str] = None,
    ) -> str:
        """Combine system, context, and prompt into a single string for CLI mode."""
        parts = []

        if system:
            parts.append(f"<system>\n{system}\n</system>\n")

        if context:
            context_str = json.dumps(context, indent=2, ensure_ascii=False)
            parts.append(f"<context>\n{context_str}\n</context>\n")

        parts.append(prompt)
        return "\n".join(parts)


class AnthropicAPIBackend(AIBackendBase):
    """Uses Anthropic API directly"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed")

    def run_prompt(
        self,
        prompt: str,
        context: Optional[dict] = None,
        system: Optional[str] = None,
    ) -> str:
        """Run prompt via Anthropic API"""
        messages = []

        if context:
            context_str = json.dumps(context, indent=2, ensure_ascii=False)
            messages.append({
                "role": "user",
                "content": f"Context:\n```json\n{context_str}\n```\n\n{prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def run_interactive(
        self,
        prompt: str,
        context: Optional[dict] = None,
        system: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Run with streaming"""
        messages = []

        if context:
            context_str = json.dumps(context, indent=2, ensure_ascii=False)
            messages.append({
                "role": "user",
                "content": f"Context:\n```json\n{context_str}\n```\n\n{prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    def run_conversation(
        self,
        messages: list[dict],
        system: Optional[str] = None,
    ) -> str:
        """Run a multi-turn conversation via API"""
        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text


def get_backend_instance(backend: AIBackend) -> AIBackendBase:
    """Get appropriate backend instance"""
    if backend == AIBackend.CLAUDE_CODE:
        return ClaudeCodeBackend()
    elif backend == AIBackend.ANTHROPIC_API:
        return AnthropicAPIBackend()
    else:
        raise ValueError("No AI backend available")
