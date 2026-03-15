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
    catalog = build_catalog(fetch_sitemap=False, extra_urls=["https://docs.agno.com/agents"])
    entry = catalog["agents"]
    assert entry.title != "agents"  # seed title is human-readable, not slug-derived

def test_sitemap_unavailable_falls_back_to_seeds():
    """If sitemap fetch fails, server starts with seed entries only (no crash)."""
    from unittest.mock import patch
    with patch("mcp_agno.catalog.httpx.get", side_effect=Exception("network error")):
        catalog = build_catalog(fetch_sitemap=True)
    assert "agents" in catalog
    assert "introduction" in catalog
