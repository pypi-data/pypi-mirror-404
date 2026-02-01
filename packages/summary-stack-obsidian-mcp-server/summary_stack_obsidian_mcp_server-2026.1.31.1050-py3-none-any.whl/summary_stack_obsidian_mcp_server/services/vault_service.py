"""Client for local Obsidian vault operations via MCP-Obsidian."""

import json
import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


logger = logging.getLogger(__name__)


class VaultServiceError(Exception):
    """Error during vault operations."""

    pass


class ObsidianMCPClient:
    """Wrapper around mcp-obsidian server.

    Uses the official MCP Python SDK to spawn mcp-obsidian as a subprocess
    and communicate via stdio transport.

    Usage:
        async with ObsidianMCPClient(vault_path) as client:
            result = await client.write_note("path/to/note.md", "# Content")
    """

    def __init__(self, vault_root_path: str):
        """Initialize the client.

        Args:
            vault_root_path: Absolute path to the Obsidian vault root
        """
        self.vault_root_path = vault_root_path
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None

    async def __aenter__(self) -> "ObsidianMCPClient":
        """Start mcp-obsidian subprocess and establish connection."""
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()

        server_params = StdioServerParameters(
            command="npx",
            args=["@mauricio.wolff/mcp-obsidian@0.7.3", self.vault_root_path],
        )

        try:
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
            read_stream, write_stream = stdio_transport

            self._session = await self._exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            await self._session.initialize()

            logger.info(f"Connected to mcp-obsidian for vault: {self.vault_root_path}")

        except Exception as e:
            if self._exit_stack:
                await self._exit_stack.__aexit__(type(e), e, e.__traceback__)
            raise VaultServiceError(f"Failed to connect to mcp-obsidian: {e}") from e

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Cleanup subprocess and close connection."""
        if self._exit_stack:
            await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
            self._exit_stack = None
            self._session = None
            logger.info("Disconnected from mcp-obsidian")

    def _ensure_connected(self) -> ClientSession:
        """Ensure client is connected and return session."""
        if self._session is None:
            raise VaultServiceError("Client not connected. Use 'async with ObsidianMCPClient(...) as client:'")
        return self._session

    def _extract_error_message(self, content: list[Any]) -> str:
        """Extract error message from MCP response content."""
        if not content:
            return "Unknown error"
        first = content[0]
        return first.text if isinstance(first, TextContent) else "Unknown error"

    def _parse_response(self, content: list[Any]) -> dict[str, Any] | list[Any]:
        """Parse MCP tool response content to dict or list."""
        if not content:
            return {}

        first = content[0]
        if not isinstance(first, TextContent):
            return {}

        try:
            parsed: dict[str, Any] | list[Any] = json.loads(first.text)
            return parsed
        except json.JSONDecodeError:
            return {"message": first.text}

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | list[Any]:
        """Call a tool on the mcp-obsidian server."""
        session = self._ensure_connected()
        result = await session.call_tool(tool_name, arguments)

        if result.isError:
            error_msg = self._extract_error_message(result.content)
            raise VaultServiceError(f"MCP tool '{tool_name}' failed: {error_msg}")

        return self._parse_response(result.content)

    async def write_note(
        self,
        path: str,
        content: str,
        mode: str = "overwrite",
    ) -> dict[str, Any]:
        """Write a note to the vault.

        Args:
            path: Relative path from vault root (e.g., "folder/note.md")
            content: Note content (markdown with frontmatter)
            mode: Write mode ("overwrite", "append", "prepend")

        Returns:
            Response from mcp-obsidian
        """
        args: dict[str, Any] = {"path": path, "content": content, "mode": mode}
        result = await self._call_tool("write_note", args)
        return result if isinstance(result, dict) else {}

    async def read_note(self, path: str) -> dict[str, Any]:
        """Read note content and frontmatter."""
        result = await self._call_tool("read_note", {"path": path, "prettyPrint": False})
        return result if isinstance(result, dict) else {}

    async def search_notes(
        self,
        query: str,
        limit: int = 10,
        search_content: bool = True,
        search_frontmatter: bool = False,
    ) -> list[dict[str, Any]]:
        """Search notes by content or frontmatter."""
        result = await self._call_tool(
            "search_notes",
            {
                "query": query,
                "limit": limit,
                "searchContent": search_content,
                "searchFrontmatter": search_frontmatter,
                "prettyPrint": False,
            },
        )
        return result if isinstance(result, list) else []

    async def find_note_by_summary_stack_id(self, summary_stack_id: str) -> str | None:
        """Find note path by searching frontmatter for summary_stack_id."""
        results = await self.search_notes(
            query=summary_stack_id,
            limit=1,
            search_content=False,
            search_frontmatter=True,
        )

        if results:
            path: str | None = results[0].get("p")  # mcp-obsidian uses abbreviated keys
            if path and isinstance(path, str):
                logger.info(f"Found note for summary_stack {summary_stack_id} at: {path}")
                return path

        logger.warning(f"Note not found for summary_stack: {summary_stack_id}")
        return None
