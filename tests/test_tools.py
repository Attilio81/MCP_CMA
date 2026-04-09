from mcp_claude.catalog import CatalogEntry
from mcp_claude.cache import Cache
from mcp_claude.tools import (
    list_claude_sections, get_claude_page, search_claude_docs,
    MAX_CONTENT_CHARS, TRUNCATION_NOTE,
)

BASE = "https://platform.claude.com/docs/en/managed-agents"

CATALOG = {
    "overview": CatalogEntry("overview", f"{BASE}/overview", "Overview", "Overview of Managed Agents"),
    "sessions": CatalogEntry("sessions", f"{BASE}/sessions", "Sessions", ""),
}


def test_list_sections_includes_all_slugs():
    result = list_claude_sections(CATALOG)
    assert "overview" in result
    assert "sessions" in result


def test_list_sections_omits_empty_description():
    result = list_claude_sections(CATALOG)
    lines = result.strip().splitlines()
    sessions_line = next(l for l in lines if "sessions" in l)
    overview_line = next(l for l in lines if "overview" in l)
    assert "description:" in overview_line
    assert "description:" not in sessions_line


def test_list_sections_format():
    result = list_claude_sections(CATALOG)
    assert "slug: overview" in result
    assert f"url: {BASE}/overview" in result


# ---------------------------------------------------------------------------
# get_claude_page
# ---------------------------------------------------------------------------
from unittest.mock import patch


def test_get_page_by_slug():
    cache = Cache()
    with patch("mcp_claude.tools.fetch_page", return_value="overview content"):
        result = get_claude_page("overview", CATALOG, cache)
    assert result == "overview content"


def test_get_page_uses_cache():
    cache = Cache()
    cache.set(f"{BASE}/overview", "cached content")
    with patch("mcp_claude.tools.fetch_page") as mock_fetch:
        result = get_claude_page("overview", CATALOG, cache)
    mock_fetch.assert_not_called()
    assert result == "cached content"


def test_get_page_by_url():
    cache = Cache()
    with patch("mcp_claude.tools.fetch_page", return_value="direct content"):
        result = get_claude_page(f"{BASE}/overview", CATALOG, cache)
    assert result == "direct content"


def test_get_page_unknown_slug_returns_error():
    cache = Cache()
    result = get_claude_page("nonexistent", CATALOG, cache)
    assert result.startswith("Error:")
    assert "list_claude_sections" in result


def test_get_page_truncates_long_content():
    cache = Cache()
    long_content = "x" * 40_000
    with patch("mcp_claude.tools.fetch_page", return_value=long_content):
        result = get_claude_page("overview", CATALOG, cache)
    assert len(result) <= MAX_CONTENT_CHARS + len(TRUNCATION_NOTE)
    assert "truncated" in result.lower()


# ---------------------------------------------------------------------------
# search_claude_docs
# ---------------------------------------------------------------------------

def test_search_scores_by_keyword():
    """search returns metadata only — no fetch, just slug/url in output."""
    cache = Cache()
    result = search_claude_docs("overview", CATALOG, cache)
    assert "overview" in result
    assert "get_claude_page" in result  # hint to caller


def test_search_no_match_returns_no_results_message():
    cache = Cache()
    result = search_claude_docs("zzznomatch999", CATALOG, cache)
    assert "No results found" in result


def test_search_partial_fetch_failure():
    """search is lazy: no fetches happen, both entries returned as metadata."""
    catalog = {
        "overview": CatalogEntry("overview", f"{BASE}/overview", "Overview", "Overview of Managed Agents"),
        "sessions": CatalogEntry("sessions", f"{BASE}/sessions", "Sessions", "Manage session state"),
    }
    cache = Cache()
    result = search_claude_docs("manage", catalog, cache)
    assert "sessions" in result
    assert "Error" not in result


def test_search_all_fetches_fail():
    """search never fetches, so no error even if network is down."""
    cache = Cache()
    result = search_claude_docs("overview sessions", CATALOG, cache)
    assert "overview" in result
    assert "Error" not in result
