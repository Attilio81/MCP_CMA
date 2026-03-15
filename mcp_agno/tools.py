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
