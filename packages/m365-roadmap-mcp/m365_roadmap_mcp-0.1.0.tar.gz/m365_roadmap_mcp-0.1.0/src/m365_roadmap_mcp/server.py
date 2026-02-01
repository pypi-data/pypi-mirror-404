"""M365 Roadmap MCP Server - FastMCP server with stdio/HTTP transport."""

import logging
import os

from fastmcp import FastMCP

# Suppress FastMCP's INFO logs to reduce console noise
logging.getLogger("fastmcp").setLevel(logging.WARNING)

from .tools.cloud import check_cloud_availability
from .tools.details import get_feature_details
from .tools.recent import list_recent_additions
from .tools.search import search_roadmap

# Create the MCP server
mcp = FastMCP(
    "M365 Roadmap MCP",
    instructions=(
        "Query and search the Microsoft 365 Roadmap for upcoming features, "
        "release dates, and cloud instance availability.\n\n"
        "Available tools:\n"
        "- search_roadmap: Find and filter roadmap features by keyword, product, "
        "status, cloud instance (GCC, GCC High, DoD), or feature ID.\n"
        "- get_feature_details: Retrieve full metadata for a specific roadmap "
        "feature by its ID.\n"
        "- check_cloud_availability: Verify whether a feature is available for a "
        "specific cloud instance (critical for government/defense clients).\n"
        "- list_recent_additions: List features recently added to the roadmap "
        "within a given number of days."
    ),
)

# Register tools
mcp.tool(search_roadmap)
mcp.tool(get_feature_details)
mcp.tool(check_cloud_availability)
mcp.tool(list_recent_additions)


def main():
    """Run the MCP server.

    Uses stdio transport by default (for MCP client auto-start).
    Set MCP_TRANSPORT=http to run as an HTTP server for remote access.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "http":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        print(f"Starting M365 Roadmap MCP server on {host}:{port}")
        print(f"MCP endpoint: http://{host}:{port}/mcp")
        mcp.run(transport="http", host=host, port=port, show_banner=False)
    else:
        # stdio transport (default for MCP client auto-start)
        mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
