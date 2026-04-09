# MCP Claude Managed Agents

An MCP server that exposes the [Claude Managed Agents documentation](https://platform.claude.com/docs/en/managed-agents/overview) to Claude Desktop and Claude Code, keeping your AI assistant always up to date with the latest API docs.

## What it does

Provides three tools that Claude can call to read current documentation directly from `platform.claude.com`:

| Tool | Description |
|---|---|
| `list_claude_sections` | List all available Managed Agents documentation sections |
| `get_claude_page` | Fetch the full content of a documentation page by slug or URL |
| `search_claude_docs` | Search sections by keyword and get matching slugs |

**Covered sections (20 pages):** overview, quickstart, onboarding, agent-setup, tools, mcp-connector, permission-policies, skills, environments, cloud-containers, sessions, events-and-streaming, define-outcomes, vaults, github, files, memory, multi-agent, migration, observability.

The catalog is seeded at startup with all known sections and auto-discovers new pages from the live `platform.claude.com/sitemap.xml`.

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

## Installation

```bash
git clone https://github.com/Attilio81/MCP_CMA.git
cd MCP_CMA
uv pip install -e .
# or
pip install -e .
```

This installs the `mcp-claude` command.

## Claude Desktop configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "claude-docs": {
      "command": "mcp-claude"
    }
  }
}
```

If installed in a virtual environment, use the full path:

```json
{
  "mcpServers": {
    "claude-docs": {
      "command": "/path/to/venv/bin/mcp-claude"
    }
  }
}
```

Restart Claude Desktop — the three tools appear automatically.

## Claude Code configuration

```bash
claude mcp add claude-docs mcp-claude
```

Or add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "claude-docs": {
      "command": "mcp-claude"
    }
  }
}
```

## How it works

1. At startup, seed entries for all 20 known Managed Agents pages are loaded into an in-memory catalog.
2. The public sitemap at `platform.claude.com/sitemap.xml` is fetched to discover any new pages added by Anthropic. If the sitemap is unavailable, the server starts with seed entries only (no crash).
3. On each tool call, pages are fetched live from `platform.claude.com` via plain HTTP (Next.js SSR — no JavaScript rendering required).
4. Fetched content is cached in memory for the duration of the server session. Restart the server to clear the cache.

## Running tests

```bash
pip install pytest
pytest
```

## License

MIT
