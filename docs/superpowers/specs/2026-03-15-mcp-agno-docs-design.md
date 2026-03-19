# MCP Server — AGNO Documentation

**Date:** 2026-03-15
**Status:** Approved

---

## Overview

A Python MCP server that exposes AGNO framework documentation to LLMs (Claude) via tools. The server maintains a catalog of documentation URLs and fetches content on-demand, ensuring documentation is always current without storing stale copies.

---

## Architecture

The server runs as a local Python process communicating with Claude Desktop/Code via stdio (MCP protocol).

```
Claude (MCP client)
       │  stdio
       ▼
┌─────────────────────────────┐
│     agno-docs MCP Server    │
│                             │
│  ┌─────────┐  ┌──────────┐  │
│  │ Catalog │  │  Cache   │  │
│  │ (URLs)  │  │(in-memory│  │
│  └────┬────┘  └────┬─────┘  │
│       │            │        │
│  ┌────▼────────────▼─────┐  │
│  │      Tool Handler     │  │
│  │  search / get / list  │  │
│  └───────────┬───────────┘  │
│              │ httpx        │
└──────────────┼──────────────┘
               ▼
         docs.agno.com
```

**Startup sequence:**
1. Load hardcoded seed entries (known main sections), each with: `url`, `slug` (short identifier, e.g. `"agents"`), `title`, `description` (hand-written in the seed)
2. Fetch `docs.agno.com` sitemap XML to discover additional URLs by extracting `<loc>` tag values. For sitemap-discovered URLs, derive `slug` from the URL path (last path segment), set `title = slug` and `description = ""` (populated lazily on first fetch). Seed entries take precedence: if a sitemap slug collides with a seed slug, the seed entry is kept unchanged.
3. Build in-memory catalog: `dict[str, CatalogEntry]` keyed by `slug`

If the sitemap is unavailable at startup, the server logs a warning and proceeds with seed entries only. This is not a fatal error.

**CatalogEntry schema:**
```python
@dataclass
class CatalogEntry:
    slug: str         # short identifier, e.g. "agents"
    url: str          # full URL, e.g. "https://docs.agno.com/agents"
    title: str        # human-readable title
    description: str  # short description (empty string if unknown)
```

**Runtime (on-demand):**
- Tool calls trigger live fetches from `docs.agno.com`
- Fetched page content is converted to readable plain text using `html2text` configured with `ignore_links=True`, `body_width=0`, `ignore_images=True` to suppress markdown formatting and produce flat text
- All fetch calls are synchronous (`httpx.Client`, not async) for simplicity with the MCP stdio transport
- Converted content is cached in memory keyed by URL for the session duration

---

## Tools

All tools return a plain string to Claude. On error, tools return a string prefixed with `"Error: "` describing the problem — they never raise exceptions to the MCP layer.

### `list_agno_sections() -> str`
Returns a formatted plain-text list of all catalog entries.

**Output format** (one entry per line):
```
slug: agents | url: https://docs.agno.com/agents | description: Build intelligent agents with tools and memory
slug: teams  | url: https://docs.agno.com/teams  | description: Coordinate multiple agents
slug: introduction | url: https://docs.agno.com/introduction
```

The entire `| description: ...` segment is omitted from the line when description is an empty string.

### `get_agno_page(section: str) -> str`
Fetches and returns the full text content of a specific documentation page.

- **`section`**: either a catalog `slug` (e.g. `"agents"`) or a full URL (e.g. `"https://docs.agno.com/agents"`)
- **Lookup logic**: if `section` starts with `"http"`, treat as direct URL; otherwise look up by exact `slug` match in catalog. If no exact match, return `"Error: section '{section}' not found. Use list_agno_sections() to see available sections."`
- Checks cache first (keyed by resolved URL); if absent, fetches and caches
- Truncates to 32000 characters (approx. 8000 tokens at ~4 chars/token) if longer, appending: `"\n\n[Content truncated. Request a specific subsection for more detail.]"`
- On fetch error: returns `"Error: could not fetch {url}: {reason}"`

### `search_agno_docs(query: str) -> str`
Searches the catalog by keyword and returns relevant content.

- **`query`**: search string (e.g. `"memory storage"`, `"multi-agent team"`)
- **Search strategy**:
  1. Score each catalog entry: count occurrences of query words in `slug + title + description` (case-insensitive)
  2. Take top 3 entries by score (constant `TOP_N = 3`, defined in `tools.py`)
  3. Fetch content for each of the top 3 entries (using cache if available)
  4. For each fetched page, extract a 1000-character excerpt around the first keyword occurrence; if no occurrence, use the first 1000 characters
  5. If a fetch fails for one entry, skip it and continue with the remaining ones (partial results are acceptable)
- **Output format** (one result block per match):
  ```
  === agents ===
  URL: https://docs.agno.com/agents
  Excerpt: ...relevant text...

  === teams ===
  ...
  ```
- If no catalog entries match (all scores = 0): returns `"No results found for query: '{query}'. Use list_agno_sections() to browse all sections."`
- If all fetches fail: returns `"Error: could not fetch any results for query '{query}'."`

---

## Project Structure

```
mcp_agno/
├── __init__.py
├── server.py          # MCP entry point, tool registration
├── catalog.py         # CatalogEntry dataclass, seed URLs, sitemap discovery
├── fetcher.py         # httpx fetch + html2text conversion
├── cache.py           # in-memory cache: dict[str, str] (url → content)
└── tools.py           # list_agno_sections, get_agno_page, search_agno_docs
pyproject.toml         # package config
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Fetch timeout / network error | Return `"Error: could not fetch {url}: {reason}"` |
| 404 or invalid URL | Return `"Error: could not fetch {url}: HTTP 404"` |
| Sitemap unavailable at startup | Continue with seed URLs, log warning to stderr |
| Page content too long | Truncate to 32000 chars, append truncation note |
| `search_agno_docs` — one fetch fails | Skip that entry, return partial results |
| `search_agno_docs` — all fetches fail | Return error string |
| `get_agno_page` — unknown slug | Return error string with suggestion |

---

## Cache

- In-memory dict: `dict[str, str]` mapping URL → plain text content
- No TTL — cache lives for the server session; restart clears cache
- No disk persistence

---

## Dependencies

| Package | Purpose |
|---|---|
| `mcp` | Official Anthropic MCP SDK |
| `httpx` | Async HTTP fetch |
| `beautifulsoup4` | Sitemap XML parsing |
| `html2text` | HTML → plain text conversion |

---

## Package Setup (`pyproject.toml`)

```toml
[project]
name = "mcp-agno"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["mcp", "httpx", "beautifulsoup4", "html2text"]

[project.scripts]
mcp-agno = "mcp_agno.server:main"
```

Install locally with: `pip install -e .` or `uv pip install -e .`

---

## Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agno-docs": {
      "command": "python",
      "args": ["-m", "mcp_agno.server"]
    }
  }
}
```

The package must be installed in the Python environment used by `command`.

---

## Out of Scope

- Persistent index (SQLite/FTS)
- Authentication or rate limiting
- Hosted/cloud deployment
- Automatic cache invalidation / TTL
- Fuzzy/semantic search
