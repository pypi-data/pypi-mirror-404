"""Empathy Framework MCP Server.

Model Context Protocol integration for Claude Code.
Exposes Empathy workflows, agents, and telemetry as MCP tools.
"""

__version__ = "5.1.1"
__all__ = ["EmpathyMCPServer", "create_server"]

from empathy_os.mcp.server import EmpathyMCPServer, create_server
