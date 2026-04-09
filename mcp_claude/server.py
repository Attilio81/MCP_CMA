from mcp.server.fastmcp import FastMCP

from mcp_claude.cache import Cache
from mcp_claude.catalog import build_catalog
from mcp_claude import tools

# Build catalog and cache at module level (populated at server startup)
_catalog = build_catalog(fetch_sitemap=True)
_cache = Cache()

mcp = FastMCP("claude-docs")


@mcp.tool()
def list_claude_sections() -> str:
    """List all available Claude Managed Agents documentation sections with their URLs."""
    return tools.list_claude_sections(_catalog)


@mcp.tool()
def get_claude_page(section: str) -> str:
    """Fetch and return the content of a Claude Managed Agents documentation page.

    Args:
        section: A section slug (e.g. 'overview', 'sessions', 'memory') or a full URL.
    """
    return tools.get_claude_page(section, _catalog, _cache)


@mcp.tool()
def search_claude_docs(query: str) -> str:
    """Search Claude Managed Agents documentation by keyword and return relevant sections.

    Args:
        query: Search keywords (e.g. 'session state', 'multi-agent orchestration', 'vaults secrets').
    """
    return tools.search_claude_docs(query, _catalog, _cache)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
