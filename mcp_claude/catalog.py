from __future__ import annotations
import sys
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

SITEMAP_URL = "https://platform.claude.com/sitemap.xml"
BASE_URL = "https://platform.claude.com"
MANAGED_AGENTS_PREFIX = "/docs/en/managed-agents/"

SEED_ENTRIES: list[dict] = [
    {"slug": "overview",            "url": f"{BASE_URL}/docs/en/managed-agents/overview",            "title": "Overview",            "description": "Overview of Claude Managed Agents and their capabilities."},
    {"slug": "quickstart",          "url": f"{BASE_URL}/docs/en/managed-agents/quickstart",          "title": "Quickstart",          "description": "Get started quickly with your first Managed Agent."},
    {"slug": "onboarding",          "url": f"{BASE_URL}/docs/en/managed-agents/onboarding",          "title": "Onboarding",          "description": "Step-by-step onboarding guide for Managed Agents."},
    {"slug": "agent-setup",         "url": f"{BASE_URL}/docs/en/managed-agents/agent-setup",         "title": "Agent Setup",         "description": "Configure and deploy your agent."},
    {"slug": "tools",               "url": f"{BASE_URL}/docs/en/managed-agents/tools",               "title": "Tools",               "description": "Tools available to agents for performing actions."},
    {"slug": "mcp-connector",       "url": f"{BASE_URL}/docs/en/managed-agents/mcp-connector",       "title": "MCP Connector",       "description": "Integrate agents with MCP (Model Context Protocol) servers."},
    {"slug": "permission-policies", "url": f"{BASE_URL}/docs/en/managed-agents/permission-policies", "title": "Permission Policies", "description": "Define and manage agent permission policies."},
    {"slug": "skills",              "url": f"{BASE_URL}/docs/en/managed-agents/skills",              "title": "Skills",              "description": "Reusable skills and capabilities for agents."},
    {"slug": "environments",        "url": f"{BASE_URL}/docs/en/managed-agents/environments",        "title": "Environments",        "description": "Agent execution environments and configuration."},
    {"slug": "cloud-containers",    "url": f"{BASE_URL}/docs/en/managed-agents/cloud-containers",    "title": "Cloud Containers",    "description": "Run agents in secure cloud containers."},
    {"slug": "sessions",            "url": f"{BASE_URL}/docs/en/managed-agents/sessions",            "title": "Sessions",            "description": "Manage agent sessions and conversation state."},
    {"slug": "events-and-streaming","url": f"{BASE_URL}/docs/en/managed-agents/events-and-streaming","title": "Events and Streaming","description": "Stream events and real-time output from agents."},
    {"slug": "define-outcomes",     "url": f"{BASE_URL}/docs/en/managed-agents/define-outcomes",     "title": "Define Outcomes",     "description": "Define success criteria and outcomes for agents."},
    {"slug": "vaults",              "url": f"{BASE_URL}/docs/en/managed-agents/vaults",              "title": "Vaults",              "description": "Store and access secrets securely with agent vaults."},
    {"slug": "github",              "url": f"{BASE_URL}/docs/en/managed-agents/github",              "title": "GitHub",              "description": "GitHub integration for agents."},
    {"slug": "files",               "url": f"{BASE_URL}/docs/en/managed-agents/files",               "title": "Files",               "description": "Upload, manage, and access files in agents."},
    {"slug": "memory",              "url": f"{BASE_URL}/docs/en/managed-agents/memory",              "title": "Memory",              "description": "Agent memory, persistence, and knowledge management."},
    {"slug": "multi-agent",         "url": f"{BASE_URL}/docs/en/managed-agents/multi-agent",         "title": "Multi-Agent",         "description": "Orchestrate multiple agents working together."},
    {"slug": "migration",           "url": f"{BASE_URL}/docs/en/managed-agents/migration",           "title": "Migration",           "description": "Migrate existing workloads to Managed Agents."},
    {"slug": "observability",       "url": f"{BASE_URL}/docs/en/managed-agents/observability",       "title": "Observability",       "description": "Monitor, trace, and debug agents in production."},
]


@dataclass
class CatalogEntry:
    slug: str
    url: str
    title: str
    description: str


def _slug_from_url(url: str) -> str:
    """Derive slug from the last path segment of a URL (e.g. 'overview' from '.../managed-agents/overview')."""
    try:
        path = urlparse(url).path.strip("/")
        return path.split("/")[-1] if "/" in path else path
    except Exception:
        return url


def _is_managed_agents_url(url: str) -> bool:
    """Return True only for managed-agents documentation pages."""
    try:
        return urlparse(url).path.startswith(MANAGED_AGENTS_PREFIX)
    except Exception:
        return False


def _fetch_sitemap_urls() -> list[str]:
    """Fetch sitemap XML and extract managed-agents <loc> URLs. Returns [] on any error."""
    try:
        response = httpx.get(SITEMAP_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "xml")
        return [
            loc.get_text()
            for loc in soup.find_all("loc")
            if _is_managed_agents_url(loc.get_text())
        ]
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

    # Discover additional managed-agents URLs from sitemap
    sitemap_urls = _fetch_sitemap_urls() if fetch_sitemap else []
    all_extra = (extra_urls or []) + sitemap_urls

    for url in all_extra:
        if not _is_managed_agents_url(url):
            continue
        slug = _slug_from_url(url)
        if slug in catalog:
            continue  # seed wins
        catalog[slug] = CatalogEntry(slug=slug, url=url, title=slug, description="")

    return catalog
