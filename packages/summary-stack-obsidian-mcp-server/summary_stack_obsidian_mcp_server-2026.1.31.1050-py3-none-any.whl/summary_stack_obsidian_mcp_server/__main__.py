"""Entry point for running the MCP server as a module."""

from summary_stack_obsidian_mcp_server.server import mcp


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
