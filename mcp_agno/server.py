from mcp.server.fastmcp import FastMCP

from mcp_agno.cache import Cache
from mcp_agno.catalog import build_catalog
from mcp_agno import tools

# Build catalog and cache at module level (populated at server startup)
_catalog = build_catalog(fetch_sitemap=True)
_cache = Cache()

mcp = FastMCP("agno-docs")


@mcp.tool()
def list_agno_sections() -> str:
    """List all available AGNO documentation sections with their URLs."""
    return tools.list_agno_sections(_catalog)


@mcp.tool()
def get_agno_page(section: str) -> str:
    """Fetch and return the content of an AGNO documentation page.

    Args:
        section: A section slug (e.g. 'agents', 'teams') or a full URL.
    """
    return tools.get_agno_page(section, _catalog, _cache)


@mcp.tool()
def search_agno_docs(query: str) -> str:
    """Search AGNO documentation by keyword and return relevant excerpts.

    Args:
        query: Search keywords (e.g. 'memory storage', 'multi-agent team').
    """
    return tools.search_agno_docs(query, _catalog, _cache)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
