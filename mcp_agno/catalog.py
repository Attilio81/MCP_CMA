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
