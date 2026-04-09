from mcp_claude.catalog import build_catalog, CatalogEntry

def test_seed_entries_present():
    catalog = build_catalog(fetch_sitemap=False)
    assert "overview" in catalog
    assert "sessions" in catalog
    assert "memory" in catalog
    assert "quickstart" in catalog

def test_catalog_entry_fields():
    catalog = build_catalog(fetch_sitemap=False)
    entry = catalog["overview"]
    assert isinstance(entry, CatalogEntry)
    assert entry.slug == "overview"
    assert entry.url.startswith("https://platform.claude.com")
    assert entry.title != ""
    assert isinstance(entry.description, str)

def test_slug_collision_seed_wins():
    """If extra_urls returns a slug matching a seed, seed entry is kept."""
    catalog = build_catalog(
        fetch_sitemap=False,
        extra_urls=["https://platform.claude.com/docs/en/managed-agents/overview"],
    )
    entry = catalog["overview"]
    assert entry.title != "overview"  # seed title is human-readable, not slug-derived

def test_sitemap_unavailable_falls_back_to_seeds():
    """If sitemap fetch fails, server starts with seed entries only (no crash)."""
    from unittest.mock import patch
    with patch("mcp_claude.catalog.httpx.get", side_effect=Exception("network error")):
        catalog = build_catalog(fetch_sitemap=True)
    assert "overview" in catalog
    assert "memory" in catalog

def test_non_managed_agents_urls_excluded():
    """URLs outside managed-agents prefix are not added to the catalog."""
    catalog = build_catalog(
        fetch_sitemap=False,
        extra_urls=["https://platform.claude.com/docs/en/intro"],
    )
    assert "intro" not in catalog
