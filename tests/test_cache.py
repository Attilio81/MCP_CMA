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
