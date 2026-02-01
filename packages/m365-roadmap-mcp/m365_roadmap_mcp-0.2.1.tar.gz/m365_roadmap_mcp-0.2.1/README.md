# M365 Roadmap MCP Server

<!-- mcp-name: io.github.jonnybottles/m365-roadmap -->

A Python-based MCP (Model Context Protocol) server that enables AI agents to query the Microsoft 365 Roadmap programmatically.

## Strategic Rationale

For organizations relying on Microsoft 365, Teams, or SharePoint, the "Roadmap" is the single source of truth for upcoming changes. However, navigating the roadmap website manually is cumbersome and disconnected from technical planning workflows. "When is Copilot coming to GCC High?" is a question that affects multi-million dollar contracts and deployment schedules.

Existing research indicates that while RSS feeds exist, there is no tool that allows an AI agent to structurally query this data to answer complex filtering questions. A "Roadmap Scout" MCP server empowers the Agent to act as a release manager, proactively identifying features that enable new capabilities or threaten existing customizations.

## Prompt Examples

Once connected to an MCP client, you can ask questions like:

1. **Search by product and status**: "What Microsoft Teams features are currently rolling out?"
2. **Check government cloud availability**: "Is Copilot available for GCC High yet?"
3. **Find recent additions**: "Show me everything added to the M365 roadmap in the last 30 days"
4. **Get feature details**: "Tell me more about roadmap feature 534606"
5. **Government cloud planning**: "My agency is on GCC High. Which OneDrive features can we expect?"

## Installation

### Prerequisites

- **Python 3.11+**
- An MCP-compatible client (Claude Desktop, Cursor, Claude Code, GitHub Copilot CLI, etc.)

### From PyPI (recommended)

Using `uvx` (requires [uv](https://github.com/astral-sh/uv)):

```bash
uvx m365-roadmap-mcp
```

To update to the latest version:

```bash
uvx m365-roadmap-mcp@latest
```

Install uv if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

Or install with pip (no uv required):

```bash
pip install m365-roadmap-mcp

# Update to latest
pip install --upgrade m365-roadmap-mcp
```
## Quick Setup

[![Install in VS Code](https://img.shields.io/badge/Install_in-VS_Code-0078d4?style=flat-square&logo=visualstudiocode)](https://vscode.dev/redirect/mcp/install?name=m365-roadmap-mcp&config=%7B%22type%22%3A%20%22stdio%22%2C%20%22command%22%3A%20%22uvx%22%2C%20%22args%22%3A%20%5B%22m365-roadmap-mcp%22%5D%7D)
[![Install in Cursor](https://img.shields.io/badge/Install_in-Cursor-000000?style=flat-square&logo=cursor)](https://cursor.com/docs/context/mcp)
[![Install in Claude Code](https://img.shields.io/badge/Install_in-Claude_Code-9b6bff?style=flat-square&logo=anthropic)](https://code.claude.com/docs/en/mcp)
[![Install in Copilot CLI](https://img.shields.io/badge/Install_in-Copilot_CLI-28a745?style=flat-square&logo=github)](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli)

> **One-click install:** Click VS Code badge for automatic setup (requires `uv` installed)
> **Manual install:** See instructions below for Cursor, Claude Code, Copilot CLI, or Claude Desktop

## Client Configuration

### Running the server

```bash
uvx m365-roadmap-mcp
```

Or if installed with pip:

```bash
m365-roadmap-mcp
```

### Claude Desktop

Add to your Claude Desktop MCP config:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Using uvx (recommended)**

```json
{
  "mcpServers": {
    "m365-roadmap": {
      "command": "uvx",
      "args": ["m365-roadmap-mcp"]
    }
  }
}
```

**Using installed package**

```json
{
  "mcpServers": {
    "m365-roadmap": {
      "command": "m365-roadmap-mcp"
    }
  }
}
```

### Cursor

**Option 1: One-Click Install (Recommended)**

```
cursor://anysphere.cursor-deeplink/mcp/install?name=m365-roadmap-mcp&config=eyJjb21tYW5kIjogInV2eCIsICJhcmdzIjogWyJtMzY1LXJvYWRtYXAtbWNwIl19
```

**Option 2: Manual Configuration**

Add to your Cursor MCP config:

- macOS: `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Windows: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

### Claude Code

```bash
claude mcp add --transport stdio m365-roadmap -- uvx m365-roadmap-mcp
```

### GitHub Copilot CLI

Add to `~/.copilot/mcp-config.json`:

```json
{
  "mcpServers": {
    "m365-roadmap": {
      "type": "stdio",
      "command": "uvx",
      "args": ["m365-roadmap-mcp"]
    }
  }
}
```
## Features

Provides a single **`search_roadmap`** tool that handles all M365 roadmap queries. Combine any filters:

- **Keyword search** -- Find features by keyword in title/description
- **Product filter** -- Filter by product tag (Teams, SharePoint, etc.)
- **Status filter** -- Filter by status (In development, Rolling out, Launched)
- **Cloud instance filter** -- Filter by cloud instance (GCC, GCC High, DoD)
- **Feature lookup** -- Retrieve full metadata for a specific roadmap ID
- **Recent additions** -- List features added within the last N days

## Data Source

This MCP server pulls data from Microsoft's public roadmap API:

- **API Endpoint:** `https://www.microsoft.com/releasecommunications/api/v1/m365`
- **Authentication:** None required (public endpoint)
- **RSS Mirror:** `https://www.microsoft.com/microsoft-365/RoadmapFeatureRSS` (same data, RSS format)

This is the same data that powers the [Microsoft 365 Roadmap website](https://www.microsoft.com/en-us/microsoft-365/roadmap). The legacy endpoint (`roadmap-api.azurewebsites.net`) was retired in March 2025.

### Coverage and Limitations

The API returns approximately **1,900 active features** -- those currently In Development, Rolling Out, or recently Launched. This is a hard cap; older or retired features age out of the API and are no longer returned. The roadmap website may display historical features that are no longer present in the API.

There is no official Microsoft documentation for this API. It is a public, unauthenticated endpoint that the community has reverse-engineered. Microsoft Graph does not expose the public M365 roadmap (Graph's Service Communications API covers tenant-specific Message Center posts and Service Health, which is different data).

---

## License

MIT
