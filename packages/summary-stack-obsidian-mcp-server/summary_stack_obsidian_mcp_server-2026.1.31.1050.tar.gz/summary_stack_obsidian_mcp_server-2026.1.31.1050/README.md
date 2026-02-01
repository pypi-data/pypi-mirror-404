# Summary Stack Obsidian MCP Server

Local MCP server for writing Summary Stack notes to Obsidian vaults.

## Quick Start

### 1. Configure Claude Desktop or Claude Code

Add to your MCP settings:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "summary-stack-obsidian": {
      "command": "uvx",
      "args": ["--from", "summary-stack-obsidian-mcp-server", "summary-stack-obsidian-mcp"],
      "env": {
        "SUMMARY_STACK_API_URL": "https://api.summarystack.ai",
        "SUMMARY_STACK_API_KEY": "your-api-key-here",
        "SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH": "/Users/you/Obsidian/YourVault",
        "SUMMARY_STACK_TARGET_RELATIVE_FOLDER": "03_Resources/_parking_lot"
      }
    }
  }
}
```

**Claude Code** (settings.json):

```json
{
  "mcpServers": {
    "summary-stack-obsidian": {
      "command": "uvx",
      "args": ["--from", "summary-stack-obsidian-mcp-server", "summary-stack-obsidian-mcp"],
      "env": {
        "SUMMARY_STACK_API_URL": "https://api.summarystack.ai",
        "SUMMARY_STACK_API_KEY": "your-api-key-here",
        "SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH": "/Users/you/Obsidian/YourVault",
        "SUMMARY_STACK_TARGET_RELATIVE_FOLDER": "03_Resources/_parking_lot"
      }
    }
  }
}
```

### 2. Restart Claude Desktop/Code

The MCP server will be available after restart.

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUMMARY_STACK_API_URL` | Yes | Summary Stack API URL |
| `SUMMARY_STACK_API_KEY` | No | API key for authentication |
| `SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH` | Yes | Absolute path to your Obsidian vault root |
| `SUMMARY_STACK_TARGET_RELATIVE_FOLDER` | No | Relative path from vault root where notes are saved (default: vault root) |

### Example

```bash
SUMMARY_STACK_API_URL=https://api.summarystack.ai
SUMMARY_STACK_API_KEY=ss-prod-abc123
SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH=/Users/you/Obsidian/MyVault
SUMMARY_STACK_TARGET_RELATIVE_FOLDER=03_Resources/_parking_lot
```

Notes will be saved to: `/Users/you/Obsidian/MyVault/03_Resources/_parking_lot/{note-filename}.md`

## Overview

This MCP server runs on your machine and provides tools to:
- Create Summary Stack notes from URLs
- Write notes to your local Obsidian vault
- Search and query your Summary Stacks

## MCP Tools

| Tool | Description |
|------|-------------|
| `create_summary_stack` | Create a Summary Stack from a URL and save as an Obsidian note |
| `list_vault_stacks` | List Summary Stack notes in your local vault |
| `search_stacks` | Semantic search across your Summary Stacks |
| `get_stack` | Get details of a specific Summary Stack |
| `list_stacks` | List all your Summary Stacks from the API |
| `get_related_stacks` | Find related Summary Stacks |

## Alternative Installation

If you prefer to install globally instead of using uvx:

```bash
pip install summary-stack-obsidian-mcp-server
```

Then use this simpler config:

```json
{
  "mcpServers": {
    "summary-stack-obsidian": {
      "command": "summary-stack-obsidian-mcp",
      "env": {
        "SUMMARY_STACK_API_URL": "https://api.summarystack.ai",
        "SUMMARY_STACK_API_KEY": "your-api-key-here",
        "SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH": "/Users/you/Obsidian/YourVault",
        "SUMMARY_STACK_TARGET_RELATIVE_FOLDER": "03_Resources/_parking_lot"
      }
    }
  }
}
```

## Development

```bash
# Run the server locally
pnpm nx serve summary_stack_obsidian_mcp_server

# Test with MCP Inspector (interactive debugging)
pnpm nx inspect summary_stack_obsidian_mcp_server

# Run tests
pnpm nx test summary_stack_obsidian_mcp_server

# Run linter
pnpm nx lint summary_stack_obsidian_mcp_server

# Type check
pnpm nx typecheck summary_stack_obsidian_mcp_server
```

### Local Development Configuration

Create a `.env.local` file in the project directory:

```bash
# API Configuration
SUMMARY_STACK_API_URL=http://localhost:8019
SUMMARY_STACK_API_KEY=your-local-api-key

# Obsidian Vault Configuration
SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH=/path/to/your/vault
SUMMARY_STACK_TARGET_RELATIVE_FOLDER=03_Resources/_parking_lot
```

The `inspect` target will automatically load this file.
