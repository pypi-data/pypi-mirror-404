"""M365 Roadmap MCP Server - FastMCP server with stdio/HTTP transport."""

import logging
import os

from fastmcp import FastMCP

# Suppress FastMCP's INFO logs to reduce console noise
logging.getLogger("fastmcp").setLevel(logging.WARNING)

from .tools.search import search_roadmap

# Create the MCP server
mcp = FastMCP(
    "M365 Roadmap MCP",
    instructions=(
        "Query and search the Microsoft 365 Roadmap for upcoming features, "
        "release dates, and cloud instance availability.\n\n"
        "Use the search_roadmap tool with any combination of filters:\n"
        "- query: keyword search across title and description\n"
        "- product: filter by product tag (e.g. 'Teams', 'SharePoint')\n"
        "- status: filter by status ('In development', 'Rolling out', 'Launched')\n"
        "- cloud_instance: filter by cloud instance ('GCC', 'GCC High', 'DoD')\n"
        "- feature_id: retrieve a single feature by its roadmap ID\n"
        "- added_within_days: show only features added within N days\n\n"
        "Tips:\n"
        "- To get feature details, use feature_id with the roadmap ID.\n"
        "- To check cloud availability, use cloud_instance with a feature_id or "
        "product filter. The cloud_instances field in each result shows all "
        "supported instances.\n"
        "- To list recent additions, use added_within_days (e.g. 30 for last month)."
    ),
)

# Register tools
mcp.tool(search_roadmap)


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
