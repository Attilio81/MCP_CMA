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


# ---------------------------------------------------------------------------
# Phase 2: get_agno_page
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Phase 3: search_agno_docs
# ---------------------------------------------------------------------------

def test_search_scores_by_keyword():
    """search returns metadata only — no fetch, just slug/url in output."""
    cache = Cache()
    result = search_agno_docs("agents", CATALOG, cache)
    assert "agents" in result
    assert "get_agno_page" in result  # hint to caller


def test_search_no_match_returns_no_results_message():
    cache = Cache()
    result = search_agno_docs("zzznomatch999", CATALOG, cache)
    assert "No results found" in result


def test_search_partial_fetch_failure():
    """search is lazy: no fetches happen, both entries returned as metadata."""
    catalog = {
        "agents": CatalogEntry("agents", "https://docs.agno.com/agents", "Agents", "Build agents"),
        "teams":  CatalogEntry("teams",  "https://docs.agno.com/teams",  "Teams",  "Build teams"),
    }
    cache = Cache()
    result = search_agno_docs("build", catalog, cache)
    assert "agents" in result
    assert "teams" in result
    assert "Error" not in result


def test_search_all_fetches_fail():
    """search never fetches, so no error even if network is down."""
    cache = Cache()
    result = search_agno_docs("agents teams", CATALOG, cache)
    assert "agents" in result
    assert "Error" not in result
