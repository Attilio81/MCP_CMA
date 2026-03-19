# MCP AGNO Docs Server — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python MCP server that exposes AGNO framework documentation to Claude via 3 tools: list sections, get a page, search docs — all fetched live from docs.agno.com.

**Architecture:** FastMCP (stdio transport) with a synchronous httpx client. An in-memory catalog is built at startup from hardcoded seeds + sitemap discovery. Page content is fetched on-demand, converted to plain text via html2text, and cached in a dict for the session.

**Tech Stack:** Python ≥3.11, `mcp` (FastMCP), `httpx`, `beautifulsoup4`, `lxml`, `html2text`, `pytest`

**Spec:** `docs/superpowers/specs/2026-03-15-mcp-agno-docs-design.md`

---

## Chunk 1: Project scaffolding

### Task 1: Initialize package structure and pyproject.toml

**Files:**
- Create: `pyproject.toml`
- Create: `mcp_agno/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "mcp-agno"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["mcp", "httpx", "beautifulsoup4", "lxml", "html2text"]

[project.scripts]
mcp-agno = "mcp_agno.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty package files**

```python
# mcp_agno/__init__.py
# (empty)
```

```python
# tests/__init__.py
# (empty)
```

- [ ] **Step 3: Install the package in dev mode**

Run: `pip install -e .` or `uv pip install -e .`

Then verify: `python -c "import mcp_agno"` — should import with no error.

- [ ] **Step 4: Commit**

```bash
git init
git add pyproject.toml mcp_agno/__init__.py tests/__init__.py
git commit -m "chore: initialize mcp-agno package structure"
```

---

## Chunk 2: Cache module

### Task 2: In-memory cache

**Files:**
- Create: `mcp_agno/cache.py`
- Create: `tests/test_cache.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cache.py
from mcp_agno.cache import Cache

def test_cache_miss_returns_none():
    c = Cache()
    assert c.get("https://docs.agno.com/agents") is None

def test_cache_stores_and_retrieves():
    c = Cache()
    c.set("https://docs.agno.com/agents", "some content")
    assert c.get("https://docs.agno.com/agents") == "some content"

def test_cache_overwrite():
    c = Cache()
    c.set("https://docs.agno.com/agents", "old")
    c.set("https://docs.agno.com/agents", "new")
    assert c.get("https://docs.agno.com/agents") == "new"
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_cache.py -v`
Expected: `ModuleNotFoundError: No module named 'mcp_agno.cache'`

- [ ] **Step 3: Implement `cache.py`**

```python
# mcp_agno/cache.py
class Cache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, url: str) -> str | None:
        return self._store.get(url)

    def set(self, url: str, content: str) -> None:
        self._store[url] = content
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `pytest tests/test_cache.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add mcp_agno/cache.py tests/test_cache.py
git commit -m "feat: add in-memory cache module"
```

---

## Chunk 3: Catalog module

### Task 3: CatalogEntry dataclass and seed URLs

**Files:**
- Create: `mcp_agno/catalog.py`
- Create: `tests/test_catalog.py`

- [ ] **Step 1: Write failing tests for seed loading**

```python
# tests/test_catalog.py
from mcp_agno.catalog import build_catalog, CatalogEntry

def test_seed_entries_present():
    catalog = build_catalog(fetch_sitemap=False)
    assert "agents" in catalog
    assert "teams" in catalog
    assert "workflows" in catalog
    assert "introduction" in catalog

def test_catalog_entry_fields():
    catalog = build_catalog(fetch_sitemap=False)
    entry = catalog["agents"]
    assert isinstance(entry, CatalogEntry)
    assert entry.slug == "agents"
    assert entry.url.startswith("https://docs.agno.com")
    assert entry.title != ""
    assert isinstance(entry.description, str)

def test_slug_collision_seed_wins():
    """If sitemap returns a slug matching a seed, seed entry is kept."""
    # We inject a fake sitemap result that collides with "agents"
    catalog = build_catalog(fetch_sitemap=False, extra_urls=["https://docs.agno.com/agents"])
    entry = catalog["agents"]
    # Seed entry has a real title and description, not the derived slug
    assert entry.title != "agents"  # seed title is human-readable, not slug-derived

def test_sitemap_unavailable_falls_back_to_seeds():
    """If sitemap fetch fails, server starts with seed entries only (no crash)."""
    from unittest.mock import patch
    import sys, io
    with patch("mcp_agno.catalog.httpx.get", side_effect=Exception("network error")):
        catalog = build_catalog(fetch_sitemap=True)
    # Seed entries must still be present
    assert "agents" in catalog
    assert "introduction" in catalog
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_catalog.py -v`
Expected: `ImportError`

- [ ] **Step 3: Implement `catalog.py`**

```python
# mcp_agno/catalog.py
from __future__ import annotations
import sys
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

SITEMAP_URL = "https://docs.agno.com/sitemap.xml"
BASE_URL = "https://docs.agno.com"

SEED_ENTRIES: list[dict] = [
    {"slug": "introduction", "url": f"{BASE_URL}/introduction", "title": "Introduction", "description": "Overview of the AGNO framework."},
    {"slug": "agents",       "url": f"{BASE_URL}/agents",       "title": "Agents",       "description": "Build intelligent agents with tools, memory, and reasoning."},
    {"slug": "teams",        "url": f"{BASE_URL}/teams",        "title": "Teams",        "description": "Coordinate multiple agents to collaborate and reach decisions."},
    {"slug": "workflows",    "url": f"{BASE_URL}/workflows",    "title": "Workflows",    "description": "Orchestrate deterministic and agentic steps into structured systems."},
    {"slug": "agentos",      "url": f"{BASE_URL}/agentos",      "title": "AgentOS",      "description": "Deploy, govern, and operate agents in production."},
]


@dataclass
class CatalogEntry:
    slug: str
    url: str
    title: str
    description: str


def _slug_from_url(url: str) -> str:
    """Derive slug from last non-empty path segment of a URL."""
    path = url.rstrip("/").split("/")[-1]
    return path or url


def _fetch_sitemap_urls() -> list[str]:
    """Fetch sitemap XML and extract <loc> URLs. Returns [] on any error."""
    try:
        response = httpx.get(SITEMAP_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "xml")
        return [loc.get_text() for loc in soup.find_all("loc")]
    except Exception as exc:
        print(f"Warning: could not fetch sitemap: {exc}", file=sys.stderr)
        return []


def build_catalog(
    fetch_sitemap: bool = True,
    extra_urls: list[str] | None = None,
) -> dict[str, CatalogEntry]:
    """Build the in-memory catalog. Seed entries take precedence over sitemap."""
    catalog: dict[str, CatalogEntry] = {}

    # Load seeds first
    for entry in SEED_ENTRIES:
        catalog[entry["slug"]] = CatalogEntry(**entry)

    # Discover additional URLs
    sitemap_urls = _fetch_sitemap_urls() if fetch_sitemap else []
    all_extra = (extra_urls or []) + sitemap_urls

    for url in all_extra:
        slug = _slug_from_url(url)
        if slug in catalog:
            continue  # seed wins
        catalog[slug] = CatalogEntry(slug=slug, url=url, title=slug, description="")

    return catalog
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_catalog.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add mcp_agno/catalog.py tests/test_catalog.py
git commit -m "feat: add catalog module with seed entries and sitemap discovery"
```

---

## Chunk 4: Fetcher module

### Task 4: HTTP fetch + HTML-to-text conversion

**Files:**
- Create: `mcp_agno/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_fetcher.py
import httpx
from unittest.mock import MagicMock, patch
from mcp_agno.fetcher import fetch_page

SAMPLE_HTML = """
<html><body>
  <h1>Agents</h1>
  <p>Build intelligent agents with <b>tools</b> and memory.</p>
  <a href="/other">Link</a>
</body></html>
"""

def test_fetch_returns_plain_text():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = SAMPLE_HTML

    with patch("mcp_agno.fetcher.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
        result = fetch_page("https://docs.agno.com/agents")

    assert "Agents" in result
    assert "Build intelligent agents" in result
    # Links should not appear (ignore_links=True)
    assert "href" not in result
    assert "/other" not in result

def test_fetch_network_error_returns_error_string():
    with patch("mcp_agno.fetcher.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("timeout")
        result = fetch_page("https://docs.agno.com/agents")

    assert result.startswith("Error:")
    assert "docs.agno.com/agents" in result

def test_fetch_http_error_returns_error_string():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock(status_code=404)
    )
    with patch("mcp_agno.fetcher.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
        result = fetch_page("https://docs.agno.com/missing")

    assert result.startswith("Error:")
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_fetcher.py -v`
Expected: `ModuleNotFoundError: No module named 'mcp_agno.fetcher'`

- [ ] **Step 3: Implement `fetcher.py`**

```python
# mcp_agno/fetcher.py
import html2text
import httpx

_converter = html2text.HTML2Text()
_converter.ignore_links = True
_converter.ignore_images = True
_converter.body_width = 0


def fetch_page(url: str) -> str:
    """Fetch a URL and return its content as plain text. Returns 'Error: ...' on failure."""
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return _converter.handle(response.text)
    except httpx.HTTPStatusError as exc:
        return f"Error: could not fetch {url}: HTTP {exc.response.status_code}"
    except Exception as exc:
        return f"Error: could not fetch {url}: {exc}"
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_fetcher.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add mcp_agno/fetcher.py tests/test_fetcher.py
git commit -m "feat: add fetcher module with html2text conversion and error handling"
```

---

## Chunk 5: Tools module

### Task 5: list_agno_sections

**Files:**
- Create: `mcp_agno/tools.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tools.py
from mcp_agno.catalog import CatalogEntry
from mcp_agno.cache import Cache
from mcp_agno.tools import (
    list_agno_sections, get_agno_page, search_agno_docs,
    MAX_CONTENT_CHARS, TRUNCATION_NOTE,
)

CATALOG = {
    "agents": CatalogEntry("agents", "https://docs.agno.com/agents", "Agents", "Build agents"),
    "teams":  CatalogEntry("teams",  "https://docs.agno.com/teams",  "Teams",  ""),
}

def test_list_sections_includes_all_slugs():
    result = list_agno_sections(CATALOG)
    assert "agents" in result
    assert "teams" in result

def test_list_sections_omits_empty_description():
    result = list_agno_sections(CATALOG)
    lines = result.strip().splitlines()
    teams_line = next(l for l in lines if "teams" in l)
    agents_line = next(l for l in lines if "agents" in l)
    assert "description:" in agents_line
    assert "description:" not in teams_line

def test_list_sections_format():
    result = list_agno_sections(CATALOG)
    assert "slug: agents" in result
    assert "url: https://docs.agno.com/agents" in result
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_tools.py::test_list_sections_includes_all_slugs -v`
Expected: `ImportError`

- [ ] **Step 3: Implement `list_agno_sections` in `tools.py`**

```python
# mcp_agno/tools.py
from __future__ import annotations
from mcp_agno.catalog import CatalogEntry
from mcp_agno.cache import Cache
from mcp_agno.fetcher import fetch_page

TOP_N = 3
MAX_CONTENT_CHARS = 32_000
EXCERPT_CHARS = 1_000
TRUNCATION_NOTE = "\n\n[Content truncated. Request a specific subsection for more detail.]"


def list_agno_sections(catalog: dict[str, CatalogEntry]) -> str:
    lines = []
    for entry in catalog.values():
        line = f"slug: {entry.slug} | url: {entry.url}"
        if entry.description:
            line += f" | description: {entry.description}"
        lines.append(line)
    return "\n".join(lines)
```

- [ ] **Step 4: Run list tests**

Run: `pytest tests/test_tools.py -k "list" -v`
Expected: 3 PASSED

### Task 6: get_agno_page

- [ ] **Step 5: Write failing tests for get_agno_page**

```python
# Append to tests/test_tools.py
from unittest.mock import patch

def test_get_page_by_slug():
    cache = Cache()
    with patch("mcp_agno.tools.fetch_page", return_value="agent content"):
        result = get_agno_page("agents", CATALOG, cache)
    assert result == "agent content"

def test_get_page_uses_cache():
    cache = Cache()
    cache.set("https://docs.agno.com/agents", "cached content")
    with patch("mcp_agno.tools.fetch_page") as mock_fetch:
        result = get_agno_page("agents", CATALOG, cache)
    mock_fetch.assert_not_called()
    assert result == "cached content"

def test_get_page_by_url():
    cache = Cache()
    with patch("mcp_agno.tools.fetch_page", return_value="direct content"):
        result = get_agno_page("https://docs.agno.com/agents", CATALOG, cache)
    assert result == "direct content"

def test_get_page_unknown_slug_returns_error():
    cache = Cache()
    result = get_agno_page("nonexistent", CATALOG, cache)
    assert result.startswith("Error:")
    assert "list_agno_sections" in result

def test_get_page_truncates_long_content():
    cache = Cache()
    long_content = "x" * 40_000
    with patch("mcp_agno.tools.fetch_page", return_value=long_content):
        result = get_agno_page("agents", CATALOG, cache)
    assert len(result) <= MAX_CONTENT_CHARS + len(TRUNCATION_NOTE)
    assert "truncated" in result.lower()
```

- [ ] **Step 6: Run to confirm failure**

Run: `pytest tests/test_tools.py -k "get_page" -v`
Expected: 5 FAILED (not implemented yet)

- [ ] **Step 7: Implement `get_agno_page` in `tools.py`**

```python
def get_agno_page(section: str, catalog: dict[str, CatalogEntry], cache: Cache) -> str:
    # Resolve URL
    if section.startswith("http"):
        url = section
    elif section in catalog:
        url = catalog[section].url
    else:
        return f"Error: section '{section}' not found. Use list_agno_sections() to see available sections."

    # Check cache
    cached = cache.get(url)
    if cached is not None:
        return cached

    # Fetch
    content = fetch_page(url)

    # Truncate if needed
    if not content.startswith("Error:") and len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS] + TRUNCATION_NOTE

    # Cache only successful fetches
    if not content.startswith("Error:"):
        cache.set(url, content)

    return content
```

- [ ] **Step 8: Run get_page tests**

Run: `pytest tests/test_tools.py -k "get_page" -v`
Expected: 5 PASSED

### Task 7: search_agno_docs

- [ ] **Step 9: Write failing tests for search_agno_docs**

```python
# Append to tests/test_tools.py

def test_search_scores_by_keyword():
    cache = Cache()
    with patch("mcp_agno.tools.fetch_page", return_value="some agent content about memory"):
        result = search_agno_docs("agents", CATALOG, cache)
    assert "agents" in result
    assert "===" in result  # result block header

def test_search_no_match_returns_no_results_message():
    cache = Cache()
    result = search_agno_docs("zzznomatch999", CATALOG, cache)
    assert "No results found" in result

def test_search_partial_fetch_failure():
    """If one entry fetch fails, partial results are returned."""
    catalog = {
        "agents": CatalogEntry("agents", "https://docs.agno.com/agents", "Agents", "Build agents"),
        "teams":  CatalogEntry("teams",  "https://docs.agno.com/teams",  "Teams",  "Build teams"),
    }
    cache = Cache()

    def fake_fetch(url):
        if "agents" in url:
            return "great agent content"
        return "Error: network failure"

    with patch("mcp_agno.tools.fetch_page", side_effect=fake_fetch):
        result = search_agno_docs("build", catalog, cache)

    assert "agents" in result
    # Should still return partial results, not a total error
    assert "Error" not in result or "great agent content" in result

def test_search_all_fetches_fail():
    cache = Cache()
    with patch("mcp_agno.tools.fetch_page", return_value="Error: network failure"):
        # Need both entries to match the query
        result = search_agno_docs("agents teams", CATALOG, cache)
    assert "Error" in result
```

- [ ] **Step 10: Run to confirm failure**

Run: `pytest tests/test_tools.py -k "search" -v`
Expected: FAILED

- [ ] **Step 11: Implement `search_agno_docs` in `tools.py`**

```python
def _score_entry(entry: CatalogEntry, query_words: list[str]) -> int:
    text = f"{entry.slug} {entry.title} {entry.description}".lower()
    return sum(text.count(word) for word in query_words)


def _excerpt(content: str, query_words: list[str]) -> str:
    lower = content.lower()
    for word in query_words:
        idx = lower.find(word)
        if idx != -1:
            start = max(0, idx - 100)
            return content[start : start + EXCERPT_CHARS]
    return content[:EXCERPT_CHARS]


def search_agno_docs(query: str, catalog: dict[str, CatalogEntry], cache: Cache) -> str:
    query_words = query.lower().split()

    scored = [
        (entry, _score_entry(entry, query_words))
        for entry in catalog.values()
    ]
    scored = [(e, s) for e, s in scored if s > 0]

    if not scored:
        return f"No results found for query: '{query}'. Use list_agno_sections() to browse all sections."

    scored.sort(key=lambda x: x[1], reverse=True)
    top = [entry for entry, _ in scored[:TOP_N]]

    blocks = []
    all_failed = True

    for entry in top:
        content = get_agno_page(entry.slug, catalog, cache)
        if content.startswith("Error:"):
            continue
        all_failed = False
        excerpt = _excerpt(content, query_words)
        blocks.append(f"=== {entry.slug} ===\nURL: {entry.url}\nExcerpt: {excerpt}")

    if all_failed:
        return f"Error: could not fetch any results for query '{query}'."

    return "\n\n".join(blocks)
```

- [ ] **Step 12: Run all tools tests**

Run: `pytest tests/test_tools.py -v`
Expected: all PASSED

- [ ] **Step 13: Commit**

```bash
git add mcp_agno/tools.py tests/test_tools.py
git commit -m "feat: implement list_agno_sections, get_agno_page, search_agno_docs tools"
```

---

## Chunk 6: Server entry point

### Task 8: FastMCP server wiring

**Files:**
- Create: `mcp_agno/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write a smoke test**

```python
# tests/test_server.py
import importlib
import sys
from unittest.mock import patch

def _reload_server_patched():
    """Import server.py fresh with build_catalog patched to avoid network calls.

    Strategy: pop mcp_agno.server from sys.modules to force a fresh import,
    then import inside the patch context. Because the fresh import executes
    'from mcp_agno.catalog import build_catalog' while the patch is active,
    server.py's module-level 'build_catalog' name is bound to the mock.
    The subsequent '_catalog = build_catalog(fetch_sitemap=True)' therefore
    calls the mock — no network request.
    """
    sys.modules.pop("mcp_agno.server", None)
    with patch("mcp_agno.catalog.build_catalog", return_value={}):
        import mcp_agno.server
    return mcp_agno.server

def test_server_module_importable():
    """Server imports and runs module-level code without network calls."""
    server = _reload_server_patched()
    assert hasattr(server, "mcp")

def test_main_function_exists():
    """main() is a callable."""
    server = _reload_server_patched()
    assert callable(server.main)
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_server.py -v`
Expected: `ImportError`

- [ ] **Step 3: Implement `server.py`**

```python
# mcp_agno/server.py
from mcp.server.fastmcp import FastMCP

from mcp_agno.cache import Cache
from mcp_agno.catalog import build_catalog
from mcp_agno import tools

# Build catalog and cache at module level (populated at server startup)
_catalog = build_catalog(fetch_sitemap=True)
_cache = Cache()

mcp = FastMCP("agno-docs")


@mcp.tool()
def list_agno_sections() -> str:
    """List all available AGNO documentation sections with their URLs."""
    return tools.list_agno_sections(_catalog)


@mcp.tool()
def get_agno_page(section: str) -> str:
    """Fetch and return the content of an AGNO documentation page.

    Args:
        section: A section slug (e.g. 'agents', 'teams') or a full URL.
    """
    return tools.get_agno_page(section, _catalog, _cache)


@mcp.tool()
def search_agno_docs(query: str) -> str:
    """Search AGNO documentation by keyword and return relevant excerpts.

    Args:
        query: Search keywords (e.g. 'memory storage', 'multi-agent team').
    """
    return tools.search_agno_docs(query, _catalog, _cache)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run smoke tests**

Run: `pytest tests/test_server.py -v`
Expected: 2 PASSED

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: all tests PASSED

- [ ] **Step 6: Commit**

```bash
git add mcp_agno/server.py tests/test_server.py
git commit -m "feat: wire FastMCP server entry point with all three tools"
```

---

## Chunk 7: Integration and Claude config

### Task 9: Manual smoke test and Claude Desktop config

- [ ] **Step 1: Run the server manually to verify it starts**

Run: `python -m mcp_agno.server`

Expected: server starts with no errors (blocks waiting for stdio input — use Ctrl+C to exit). You should see the sitemap fetch warning or success in stderr.

- [ ] **Step 2: Add Claude Desktop configuration**

Find your `claude_desktop_config.json` (typically at `%APPDATA%\Claude\claude_desktop_config.json` on Windows).

Add this entry under `"mcpServers"`:

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

Ensure the `python` command refers to the environment where `mcp-agno` is installed (`pip install -e .`).

- [ ] **Step 3: Restart Claude Desktop and verify tools appear**

In Claude Desktop, check that the tools `list_agno_sections`, `get_agno_page`, and `search_agno_docs` appear in the tools list.

Test with: "List all AGNO documentation sections" — Claude should call `list_agno_sections` and return the catalog.

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "docs: add Claude Desktop config instructions in plan; project complete"
```

---

## Summary

| Module | Responsibility |
|---|---|
| `cache.py` | In-memory dict store for fetched page content |
| `catalog.py` | CatalogEntry dataclass, seed URLs, sitemap discovery |
| `fetcher.py` | httpx fetch + html2text plain text conversion |
| `tools.py` | Business logic for all 3 MCP tools |
| `server.py` | FastMCP wiring, entry point |
