import importlib
import sys
from unittest.mock import patch

def _reload_server_patched():
    """Import server.py fresh with build_catalog patched to avoid network calls.

    Strategy: pop mcp_agno.server from sys.modules to force a fresh import,
    then import inside the patch context. Because the fresh import executes
    'from mcp_agno.catalog import build_catalog' while the patch is active,
    server.py's module-level 'build_catalog' name is bound to the mock.
    The subsequent '_catalog = build_catalog(fetch_sitemap=True)' therefore
    calls the mock — no network request.
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
