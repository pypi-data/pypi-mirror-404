# M365-roadmap-mcp-server

A Model Context Protocol (MCP) server that enables AI agents to query the Microsoft 365 Roadmap programmatically.

## Strategic Rationale

For organizations relying on Microsoft 365, Teams, or SharePoint, the "Roadmap" is the single source of truth for upcoming changes. However, navigating the roadmap website manually is cumbersome and disconnected from technical planning workflows. "When is Copilot coming to GCC High?" is a question that affects multi-million dollar contracts and deployment schedules.

Existing research indicates that while RSS feeds exist, there is no tool that allows an AI agent to structurally query this data to answer complex filtering questions. A "Roadmap Scout" MCP server empowers the Agent to act as a release manager, proactively identifying features that enable new capabilities or threaten existing customizations.

## example MCP server

** NOTE THE EXAMPLE MCP SERVER IS THE WAY WE SHOULD MODEL OUR MCP SERVER FOR THIS PROJECT 

## Data Source

This MCP server pulls data from Microsoft's public roadmap API:

- **API Endpoint:** `https://www.microsoft.com/releasecommunications/api/v1/m365`
- **Authentication:** None required (public endpoint)
- **RSS Mirror:** `https://www.microsoft.com/microsoft-365/RoadmapFeatureRSS` (same data, RSS format)

This is the same data that powers the [Microsoft 365 Roadmap website](https://www.microsoft.com/en-us/microsoft-365/roadmap). The legacy endpoint (`roadmap-api.azurewebsites.net`) was retired in March 2025.

### Coverage and Limitations

The API returns approximately **1,900 active features** -- those currently In Development, Rolling Out, or recently Launched. This is a hard cap; older or retired features age out of the API and are no longer returned. The roadmap website may display historical features that are no longer present in the API.

There is no official Microsoft documentation for this API. It is a public, unauthenticated endpoint that the community has reverse-engineered. Microsoft Graph does not expose the public M365 roadmap (Graph's Service Communications API covers tenant-specific Message Center posts and Service Health, which is different data).

### Schema

The API returns a JSON array where each item represents a feature:

| Field | Description |
|-------|-------------|
| `id` | Unique Roadmap ID (e.g., "93182") |
| `title` | Feature title |
| `description` | HTML/Text description |
| `status` | Enumerated values like "In development", "Rolling out", "Launched" |
| `tags` | Product associations (e.g., "Microsoft Teams", "SharePoint") |
| `publicDisclosureAvailabilityDate` | The estimated release target |
| `cloudInstances` | Critical for government/defense clients. Values include "Worldwide (Standard Multi-Tenant)", "DoD", "GCC" |

## Proposed Tool Definitions

| Tool Name | Description | Arguments (JSON Schema) | Expected Output |
|-----------|-------------|------------------------|-----------------|
| `search_roadmap` | Searches the M365 roadmap for features matching keywords and filters | `{ "query": "string", "product": "string", "status": "string" }` | List of feature summaries with IDs and dates |
| `get_feature_details` | Retrieves the full metadata for a specific roadmap ID | `{ "feature_id": "string" }` | Detailed JSON object including description and instance tags |
| `check_cloud_availability` | Verifies if a feature is scheduled for a specific cloud instance | `{ "feature_id": "string", "instance": "string (e.g., GCC)" }` | Boolean availability and specific release date for that instance |
| `list_recent_additions` | Lists features added to the roadmap in the last X days | `{ "days": "integer" }` | List of new features to monitor |

## Example Prompts

Here are 10 prompts you can use with an AI agent connected to this MCP server:

1. **"What Microsoft Teams features are currently rolling out?"**
   Uses `search_roadmap` with product and status filters to find Teams features in active rollout.

2. **"Is Copilot available for GCC High yet?"**
   Uses `search_roadmap` to find Copilot features, then `check_cloud_availability` to verify GCC High support for each result.

3. **"Show me everything added to the M365 roadmap in the last 30 days."**
   Uses `list_recent_additions(days=30)` to surface newly announced features.

4. **"Tell me more about that Microsoft Lists agent feature you just found."**
   After a prior search, the agent uses `get_feature_details` with the ID from the earlier result to retrieve the full description, cloud instances, and release date.

5. **"Which SharePoint features are in development and available for DoD?"**
   Uses `search_roadmap` with `product="SharePoint"`, `status="In development"`, and `cloud_instance="DoD"` to combine all three filters.

6. **"Compare GCC and GCC High availability for feature 412718."**
   Uses `check_cloud_availability` twice -- once with `instance="GCC"` and once with `instance="GCC High"` -- to compare cloud parity for a single feature.

7. **"What new features were added to the roadmap this week?"**
   Uses `list_recent_additions(days=7)` to get a concise list of the latest additions for a weekly briefing.

8. **"Find all roadmap features related to data loss prevention."**
   Uses `search_roadmap(query="data loss prevention")` to keyword-search across titles and descriptions.

9. **"My agency is on GCC High. Which OneDrive features can we expect?"**
   Uses `search_roadmap` with `product="OneDrive"` and `cloud_instance="GCC High"` to find features available for that government cloud.

10. **"List all launched Viva features and check which ones support GCC."**
    Uses `search_roadmap(product="Viva", status="Launched")` to get candidates, then `check_cloud_availability` on each to filter for GCC support.

## Usage Narrative: Government Compliance Checking

### Scenario

An IT Director for a federal agency (using the GCC High cloud) asks about the availability of a new "Microsoft Lists" feature they saw in a demo.

**User Query:** "My agency is on GCC High. When will we get the new 'Microsoft Lists' agent capabilities?"

### Agent Action

1. **Analysis:** The Agent parses the intent: Product="Microsoft Lists", Feature="agent capabilities", Constraint="GCC High"

2. **Tool Call:** `search_roadmap(query="Lists agent", product="Microsoft Lists")`

3. **Data Retrieval:** The server queries the API. It finds Roadmap ID 534606: "Enables effortless list creation for Copilot users..."

4. **Tool Call:** `check_cloud_availability(feature_id="534606", instance="GCC High")`

5. **Logic:** The server inspects the `cloudInstances` array of the feature object. It looks for "GCC High"

6. **Result:** The array contains "Worldwide (Standard Multi-Tenant)". It does not contain "GCC High"

7. **Synthesis:** The Agent formulates a precise answer

### Response

> "Currently, Roadmap ID 534606 is listed for 'Worldwide (Standard Multi-Tenant)' with a status of 'Rolling Out'. It has not yet been scheduled for the GCC High environment. Based on typical parity delays, this feature is likely 6-12 months away for your tenant."