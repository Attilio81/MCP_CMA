from __future__ import annotations
from mcp_claude.catalog import CatalogEntry
from mcp_claude.cache import Cache
from mcp_claude.fetcher import fetch_page

TOP_N = 5
MAX_CONTENT_CHARS = 20_000
TRUNCATION_NOTE = "\n\n[Content truncated. Use get_claude_page() with a more specific section slug for full content.]"


def list_claude_sections(catalog: dict[str, CatalogEntry]) -> str:
    lines = []
    for entry in catalog.values():
        line = f"slug: {entry.slug} | url: {entry.url}"
        if entry.description:
            line += f" | description: {entry.description}"
        lines.append(line)
    return "\n".join(lines)


def get_claude_page(section: str, catalog: dict[str, CatalogEntry], cache: Cache) -> str:
    # Resolve URL
    if section.startswith("http"):
        url = section
    elif section in catalog:
        url = catalog[section].url
    else:
        return f"Error: section '{section}' not found. Use list_claude_sections() to see available sections."

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


def _score_entry(entry: CatalogEntry, query_words: list[str]) -> int:
    text = f"{entry.slug} {entry.title} {entry.description}".lower()
    return sum(text.count(word) for word in query_words)


def search_claude_docs(query: str, catalog: dict[str, CatalogEntry], cache: Cache) -> str:
    """Return matching section metadata only — no page fetching.

    The LLM should call get_claude_page() on the slug it needs after reviewing results.
    This keeps token usage minimal: search costs ~0 tokens beyond the result list.
    """
    query_words = query.lower().split()

    scored = [
        (entry, _score_entry(entry, query_words))
        for entry in catalog.values()
    ]
    scored = [(e, s) for e, s in scored if s > 0]

    if not scored:
        return f"No results found for '{query}'. Use list_claude_sections() to browse all sections."

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:TOP_N]

    lines = [f"Top {len(top)} results for '{query}' (call get_claude_page(slug) to read content):\n"]
    for entry, score in top:
        desc = f" — {entry.description}" if entry.description else ""
        lines.append(f"  slug: {entry.slug} | url: {entry.url}{desc}")

    return "\n".join(lines)
