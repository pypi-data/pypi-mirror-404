# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server that enables AI agents to query the Microsoft 365 Roadmap programmatically. The server provides structured access to Microsoft's public roadmap API, allowing agents to answer complex filtering questions about upcoming M365 features, release dates, and cloud instance availability (particularly critical for government/defense clients using GCC, GCC High, or DoD instances).

**Key API Endpoint**: `https://www.microsoft.com/releasecommunications/api/v1/m365` (replaces legacy roadmap-api.azurewebsites.net)

## Architecture Pattern

This project follows a standard MCP server architecture:

### Directory Structure
```
src/
  <server_name>_mcp/
    server.py           # FastMCP server initialization with stdio/HTTP transport
    models/             # Pydantic models for data structures
    feeds/              # Data fetching and parsing logic
    tools/              # MCP tool implementations (async functions)
      __init__.py
      <tool_name>.py    # Each tool in its own module
tests/
  test_tools.py         # pytest-based tests for MCP tools
  test_feeds.py         # Tests for data fetching
```

### Core Components

**1. Server Entry Point (`server.py`)**
- Uses FastMCP library for MCP protocol implementation
- Supports dual transport: stdio (default for MCP client auto-start) and HTTP (for remote access)
- Transport selection via `MCP_TRANSPORT` environment variable
- Registers tools using `mcp.tool()` decorator
- Includes server instructions for AI agents

**2. Tool Implementation Pattern**
- Each tool is an async function in `tools/` directory
- Tools accept typed parameters (leveraging Python type hints)
- Return structured dictionaries with results
- Include comprehensive docstrings describing usage, parameters, and return values
- Example tool structure:
  ```python
  async def tool_name(
      param1: str | None = None,
      param2: int = 10,
  ) -> dict:
      """Tool description.

      Args:
          param1: Description
          param2: Description

      Returns:
          Dictionary with results
      """
  ```

**3. Data Models (`models/`)**
- Pydantic BaseModel classes for type safety and validation
- Include `to_dict()` methods for serialization
- Use Field() with descriptions for clarity

**4. Data Fetching (`feeds/`)**
- Async functions using httpx for HTTP requests
- RSS/API parsing logic separated from tool logic
- Returns strongly-typed model objects

## Tool Definitions

**`search_roadmap`** - Single tool for all M365 roadmap queries. All parameters are optional and can be combined.
- Args:
  - query (str) - keyword search across title and description
  - product (str) - filter by product tag (e.g. "Teams", "SharePoint")
  - status (str) - filter by status ("In development", "Rolling out", "Launched")
  - cloud_instance (str) - filter by cloud instance ("GCC", "GCC High", "DoD")
  - feature_id (str) - retrieve a single feature by its roadmap ID (ignores other filters)
  - added_within_days (int) - only return features added within N days (clamped 1-365)
  - limit (int, default=10, max=100) - max results returned
- Returns: dict with total_found, features list, filters_applied
- Feature details: use `feature_id` to look up a specific feature
- Cloud availability: each feature includes `cloud_instances` list; combine with `cloud_instance` filter
- Recent additions: use `added_within_days` (e.g. 30 for last month)

## Key Schema Fields from M365 API

Critical fields from the API response:
- `id` - Unique Roadmap ID
- `title` - Feature title
- `description` - HTML/Text description
- `status` - Values: "In development", "Rolling out", "Launched"
- `tags` - Product associations (e.g., "Microsoft Teams", "SharePoint")
- `publicDisclosureAvailabilityDate` - Estimated release target
- `cloudInstances` - Critical for government clients: "Worldwide (Standard Multi-Tenant)", "DoD", "GCC", "GCC High"

## Development Commands

**Testing**
```bash
pytest                          # Run all tests
pytest tests/test_tools.py      # Run specific test file
pytest -k test_name             # Run specific test by name
pytest -v                       # Verbose output
```

**Running the Server**

Stdio mode (default for MCP clients):
```bash
python -m <server_name>_mcp.server
```

HTTP mode (for remote access):
```bash
MCP_TRANSPORT=http python -m <server_name>_mcp.server
# Custom host/port:
MCP_TRANSPORT=http MCP_HOST=0.0.0.0 MCP_PORT=8000 python -m <server_name>_mcp.server
```

## Testing Approach

- Use pytest with `@pytest.mark.asyncio` for async tests
- Test each tool with multiple filter combinations
- Include edge cases: invalid dates, nonexistent IDs, empty results
- Verify filter composition (multiple filters combined)
- Test boundary conditions (limit clamping, date ranges)
- Structure: One test file per module (test_tools.py, test_feeds.py)

## Implementation Notes

1. **Follow the Established Architecture**: The directory structure and patterns in `src/m365_roadmap_mcp/` define the standard to follow
2. **Async-First**: All tools and data fetching should be async
3. **Filter Composition**: Support combining multiple filters (see search.py for pattern)
4. **Error Handling**: Return error messages in `filters_applied` dict rather than raising exceptions
5. **Case-Insensitive Matching**: Use `.lower()` for all string comparisons
6. **Government Cloud Focus**: The `cloudInstances` field is critical for compliance - prioritize accurate filtering
7. **Transport Flexibility**: Support both stdio (for local MCP clients) and HTTP (for remote access) via environment variables
