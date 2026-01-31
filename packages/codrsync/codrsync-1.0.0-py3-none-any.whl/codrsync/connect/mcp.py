"""
MCP connector - detect configured MCP servers and suggest new ones based on stack.
"""

import json
from pathlib import Path

from codrsync.connect.base import ConnectorBase, ConnectorResult


# MCP server suggestions based on detected stack
STACK_MCP_SUGGESTIONS: dict[str, list[str]] = {
    "Supabase": ["supabase-mcp"],
    "PostgreSQL": ["postgres-mcp"],
    "GitHub Actions": ["github-mcp"],
    "Docker": ["docker-mcp"],
    "Prisma": ["prisma-mcp"],
    "Next.js": ["vercel-mcp"],
    "Vercel": ["vercel-mcp"],
    "AWS SDK": ["aws-mcp"],
    "Stripe": ["stripe-mcp"],
}


class MCPConnector(ConnectorBase):
    def service_name(self) -> str:
        return "mcp"

    def check(self, project_path: Path) -> ConnectorResult:
        details: dict = {}
        servers: list[str] = []

        # Check .claude/mcp.json (project-level)
        project_mcp = project_path / ".claude" / "mcp.json"
        if project_mcp.exists():
            found = self._read_mcp_config(project_mcp)
            servers.extend(found)
            details["project_config"] = str(project_mcp)

        # Check ~/.claude/mcp.json (global)
        global_mcp = Path.home() / ".claude" / "mcp.json"
        if global_mcp.exists():
            found = self._read_mcp_config(global_mcp)
            for s in found:
                if s not in servers:
                    servers.append(s)
            details["global_config"] = str(global_mcp)

        details["servers"] = servers
        details["count"] = len(servers)

        connected = len(servers) > 0

        return ConnectorResult(
            service="mcp",
            connected=connected,
            status="connected" if connected else "not_configured",
            details=details,
        )

    def _read_mcp_config(self, config_path: Path) -> list[str]:
        """Read MCP config and return list of server names."""
        try:
            with open(config_path) as f:
                data = json.load(f)
            # MCP config format: {"mcpServers": {"name": {...}}}
            mcp_servers = data.get("mcpServers", {})
            return list(mcp_servers.keys())
        except (json.JSONDecodeError, OSError):
            return []

    @staticmethod
    def suggest_for_stack(detected_tools: list[str]) -> list[str]:
        """Suggest MCP servers based on detected stack."""
        suggestions = []
        for tool in detected_tools:
            for key, mcps in STACK_MCP_SUGGESTIONS.items():
                if key.lower() in tool.lower():
                    for mcp in mcps:
                        if mcp not in suggestions:
                            suggestions.append(mcp)
        return suggestions
