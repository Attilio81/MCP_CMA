from mcp_claude.cache import Cache

BASE = "https://platform.claude.com/docs/en/managed-agents"


def test_cache_miss_returns_none():
    c = Cache()
    assert c.get(f"{BASE}/overview") is None


def test_cache_stores_and_retrieves():
    c = Cache()
    c.set(f"{BASE}/overview", "some content")
    assert c.get(f"{BASE}/overview") == "some content"


def test_cache_overwrite():
    c = Cache()
    c.set(f"{BASE}/overview", "old")
    c.set(f"{BASE}/overview", "new")
    assert c.get(f"{BASE}/overview") == "new"
