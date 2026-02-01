"""MCP Server for creating Summary Stack notes in local Obsidian vaults."""

import logging
from pathlib import Path

from fastmcp import FastMCP
from summary_stack_mcp_core import (
    get_related_stacks,
    get_stack,
    list_stacks,
    search_stacks,
)

from summary_stack_obsidian_mcp_server.config import load_config
from summary_stack_obsidian_mcp_server.services import (
    ObsidianMCPClient,
    SummaryStackAPIClient,
)


logger = logging.getLogger(__name__)


def _generate_related_notes_section(relationships: list[dict]) -> str:
    """Generate Related Notes markdown section.

    Args:
        relationships: List of validated relationship dicts with target_title and path

    Returns:
        Markdown section string to append to note content
    """
    if not relationships:
        return "\n## Related Notes\n\n*No related notes discovered yet.*\n"

    lines = ["\n## Related Notes\n"]
    for rel in relationships:
        # Use actual filename from vault path for wiki-link
        vault_path = rel.get("path", "")
        filename = Path(vault_path).stem if vault_path else rel["target_title"]
        wiki_link = f"[[{filename}|{rel['target_title']}]]"
        lines.append(f"- {wiki_link}")

    lines.append("")
    return "\n".join(lines)


mcp = FastMCP("summary-stack-obsidian")

# Register core tools from summary_stack_mcp_core
mcp.tool()(search_stacks)
mcp.tool()(get_stack)
mcp.tool()(list_stacks)
mcp.tool()(get_related_stacks)


@mcp.tool
async def create_summary_stack(url: str) -> str:
    """Create a Summary Stack from a URL and save it as an Obsidian note.

    Processes the URL through the Summary Stack API and generates a structured note.
    Related notes are validated against the local vault before linking - only notes
    that physically exist will be included in the Related Notes section.

    Args:
        url: URL to process into a Summary Stack note

    Returns:
        Summary of the created note including path and related notes count
    """
    config = load_config()

    api_client = SummaryStackAPIClient(config.api_url, config.api_key)

    # Step 1: Get manifest from API (markdown has no Related Notes section)
    logger.info(f"Creating summary stack for URL: {url}")
    manifest = await api_client.create_obsidian_manifest(url)

    # Step 2: Validate relationships against local vault and build note
    validated_relationships: list[dict] = []
    async with ObsidianMCPClient(config.vault_root_path) as client:
        # Validate each relationship - only include if note exists in vault
        if manifest.relationships:
            for rel in manifest.relationships:
                existing_path = await client.find_note_by_summary_stack_id(rel.target_summary_stack_id)
                if existing_path:
                    validated_relationships.append(
                        {
                            "target_title": rel.target_title,
                            "path": existing_path,
                        }
                    )
                else:
                    logger.info(f"Skipping relationship to '{rel.target_title}' - note not found in vault")

        # Step 3: Append validated Related Notes section to markdown
        related_notes_section = _generate_related_notes_section(validated_relationships)
        full_content = manifest.markdown_content + related_notes_section

        # Step 4: Construct note path
        note_path = f"{config.target_relative_folder}/{manifest.filename}" if config.target_relative_folder else manifest.filename

        # Step 5: Write note to vault
        logger.info(f"Writing note to vault: {note_path}")
        await client.write_note(note_path, full_content)

    skipped_count = len(manifest.relationships or []) - len(validated_relationships)

    result = f"Created Summary Stack note:\n  Title: {manifest.title}\n  Path: {note_path}\n  ID: {manifest.summary_stack_id}\n  Related notes linked: {len(validated_relationships)}"
    if skipped_count > 0:
        result += f"\n  Skipped (not in vault): {skipped_count}"

    return result


@mcp.tool
async def list_vault_stacks(limit: int = 10) -> str:
    """List Summary Stack notes in your local Obsidian vault.

    Scans the vault for notes with summary_stack_id in frontmatter.
    Use 'list_stacks' to list stacks from the API instead.

    Args:
        limit: Maximum number of notes to return (default: 10)

    Returns:
        List of Summary Stack note paths found in the vault
    """
    config = load_config()

    async with ObsidianMCPClient(config.vault_root_path) as client:
        results = await client.search_notes(
            query="summary_stack_id",
            limit=limit,
            search_content=False,
            search_frontmatter=True,
        )

        if not results:
            return "No Summary Stack notes found in vault"

        lines = [f"Found {len(results)} Summary Stack note(s):"]
        for note in results:
            lines.append(f"  - {note.get('path', 'unknown')}")

        return "\n".join(lines)
