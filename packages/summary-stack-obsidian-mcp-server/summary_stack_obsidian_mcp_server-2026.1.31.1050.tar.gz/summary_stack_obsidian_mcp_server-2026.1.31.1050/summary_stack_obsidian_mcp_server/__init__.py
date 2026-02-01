"""Summary Stack Obsidian MCP Server.

MCP server for creating Summary Stack notes in local Obsidian vaults.
"""

from summary_stack_obsidian_mcp_server.__main__ import main
from summary_stack_obsidian_mcp_server.server import mcp


__all__ = ["main", "mcp"]
