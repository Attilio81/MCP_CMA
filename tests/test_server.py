import importlib
import sys
from unittest.mock import patch

def _reload_server_patched():
    """Import server.py fresh with build_catalog patched to avoid network calls.

    patch("mcp_agno.catalog.build_catalog") temporarily replaces the attribute
    on the already-cached mcp_agno.catalog module object. When the fresh server
    import then executes 'from mcp_agno.catalog import build_catalog', it reads
    that attribute from the live module object and gets the mock. So the
    module-level '_catalog = build_catalog(fetch_sitemap=True)' in server.py
    calls the mock — no network request is made.
    """
    sys.modules.pop("mcp_agno.server", None)
    with patch("mcp_agno.catalog.build_catalog", return_value={}):
        import mcp_agno.server
    return mcp_agno.server

def test_server_module_importable():
    """Server imports and runs module-level code without network calls."""
    server = _reload_server_patched()
    assert hasattr(server, "mcp")

def test_main_function_exists():
    """main() is a callable."""
    server = _reload_server_patched()
    assert callable(server.main)
