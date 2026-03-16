# mcp-agno

An MCP (Model Context Protocol) server that gives AI assistants direct access to the [AGNO](https://docs.agno.com) framework documentation.

Instead of crawling docs manually or relying on outdated training data, Claude and other MCP-compatible clients can browse, fetch, and search AGNO docs in real time.

## What it does

Exposes three MCP tools:

| Tool | Description |
|------|-------------|
| `list_agno_sections` | List all available documentation sections with their slugs and URLs |
| `get_agno_page` | Fetch the full content of a documentation page by slug or URL |
| `search_agno_docs` | Keyword search across the catalog — returns matching slugs without fetching pages |

On startup the server seeds a catalog of core sections (Introduction, Agents, Teams, Workflows, AgentOS) and auto-discovers additional pages from the live AGNO sitemap.

---

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

---

## Installation

### With uv (recommended)

```bash
git clone https://github.com/Attilio81/MCP_AGNO.git
cd MCP_AGNO
uv pip install -e .
```

### With pip

```bash
git clone https://github.com/Attilio81/MCP_AGNO.git
cd MCP_AGNO
pip install -e .
```

This installs the `mcp-agno` command.

---

## Usage with Claude Desktop

Add the server to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agno-docs": {
      "command": "mcp-agno"
    }
  }
}
```

If you installed with uv in a virtual environment, use the full path:

```json
{
  "mcpServers": {
    "agno-docs": {
      "command": "/path/to/venv/bin/mcp-agno"
    }
  }
}
```

Restart Claude Desktop. The three tools will appear automatically.

---

## Usage with Claude Code (CLI)

```bash
claude mcp add agno-docs mcp-agno
```

Or add it to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "agno-docs": {
      "command": "mcp-agno"
    }
  }
}
```

---

## Running manually (for testing)

```bash
mcp-agno
```

The server runs over stdio and waits for MCP messages.

---

## Development

```bash
git clone https://github.com/Attilio81/MCP_AGNO.git
cd MCP_AGNO
uv pip install -e ".[dev]"
pytest
```

---

## License

MIT
