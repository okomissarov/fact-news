"""Optional MCP adapter. Install with: pip install 'mcp>=1,<2'

Local stdio is the recommended starting point; HTTP requires access controls
before exposure to untrusted networks.
"""
from mcp.server.fastmcp import FastMCP
from .sources import datadawn_recent_register, usaspending_agencies, gdelt_articles

mcp = FastMCP("Fact News")

@mcp.tool()
def recent_federal_register(limit: int = 10) -> dict:
    """Find most recently published Federal Register records, via DataDawn.
    These are aggregated official records; verify consequential claims at html_url.
    """
    return datadawn_recent_register(limit=limit)

@mcp.tool()
def federal_agency_reference() -> dict:
    """Get USAspending's official list of top-tier federal agencies."""
    return usaspending_agencies()

@mcp.tool()
def discover_news_articles(query: str, timespan: str = "24h", limit: int = 10) -> dict:
    """Discover GDELT-indexed reports. Headlines do not prove reported events."""
    return gdelt_articles(query=query, timespan=timespan, limit=limit)

def main():
    # STDIO for local agent integration; do NOT publicly expose without auth.
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
