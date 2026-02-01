"""Tests for MCP tools."""

import pytest


# ---------------------------------------------------------------------------
# search_roadmap
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_no_filters_returns_recent():
    """When called with no filters, returns the most recent features."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(limit=5)

    assert isinstance(result, dict)
    assert "total_found" in result
    assert "features" in result
    assert "filters_applied" in result
    assert len(result["features"]) <= 5


@pytest.mark.asyncio
async def test_search_by_keyword():
    """Keyword filter matches title or description."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(query="Microsoft", limit=5)

    assert isinstance(result["features"], list)
    for feature in result["features"]:
        text = (feature["title"] + feature["description"]).lower()
        assert "microsoft" in text
    assert result["filters_applied"].get("query") == "Microsoft"


@pytest.mark.asyncio
async def test_search_by_product():
    """Product filter returns features tagged with the given product."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(product="Teams", limit=5)

    assert isinstance(result["features"], list)
    assert len(result["features"]) <= 5
    for feature in result["features"]:
        assert any("teams" in tag.lower() for tag in feature["tags"])
    assert result["filters_applied"].get("product") == "Teams"


@pytest.mark.asyncio
async def test_search_by_status():
    """Status filter returns only matching status."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(status="In development", limit=5)

    for feature in result["features"]:
        assert feature["status"].lower() == "in development"
    assert result["filters_applied"].get("status") == "In development"


@pytest.mark.asyncio
async def test_search_by_cloud_instance():
    """Cloud instance filter returns features available for that instance."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(cloud_instance="GCC", limit=5)

    assert isinstance(result["features"], list)
    for feature in result["features"]:
        assert any("gcc" in ci.lower() for ci in feature["cloud_instances"])
    assert result["filters_applied"].get("cloud_instance") == "GCC"


@pytest.mark.asyncio
async def test_search_by_feature_id():
    """Feature ID lookup retrieves a single specific feature."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    # First get a valid ID
    recent = await search_roadmap(limit=1)
    if recent["features"]:
        fid = recent["features"][0]["id"]
        result = await search_roadmap(feature_id=fid)

        assert result["total_found"] == 1
        assert result["features"][0]["id"] == fid
        assert result["filters_applied"].get("feature_id") == fid


@pytest.mark.asyncio
async def test_search_by_feature_id_not_found():
    """Feature ID lookup for nonexistent ID returns empty results."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(feature_id="nonexistent-id-99999")

    assert result["total_found"] == 0
    assert result["features"] == []


@pytest.mark.asyncio
async def test_search_combined_filters():
    """Multiple filters can be combined."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(
        query="Microsoft",
        status="In development",
        limit=5,
    )

    assert isinstance(result, dict)
    for feature in result["features"]:
        text = (feature["title"] + feature["description"]).lower()
        assert "microsoft" in text
        assert feature["status"].lower() == "in development"


@pytest.mark.asyncio
async def test_search_limit_clamping():
    """Limit is clamped between 1 and 100."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result_low = await search_roadmap(limit=0)
    assert len(result_low["features"]) >= 0  # limit clamped to 1
    assert len(result_low["features"]) <= 1

    result_high = await search_roadmap(limit=999)
    assert len(result_high["features"]) <= 100


@pytest.mark.asyncio
async def test_search_output_structure():
    """Output includes all expected keys and correct types."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(limit=1)

    assert "total_found" in result
    assert "features" in result
    assert "filters_applied" in result
    assert isinstance(result["total_found"], int)
    assert isinstance(result["features"], list)
    assert isinstance(result["filters_applied"], dict)

    if result["features"]:
        feature = result["features"][0]
        assert "id" in feature
        assert "title" in feature
        assert "description" in feature
        assert "status" in feature
        assert "tags" in feature
        assert "cloud_instances" in feature
        assert "public_disclosure_date" in feature


# ---------------------------------------------------------------------------
# added_within_days
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_added_within_days_basic():
    """added_within_days returns features and reports the filter."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(added_within_days=30)

    assert isinstance(result, dict)
    assert isinstance(result["features"], list)
    assert result["filters_applied"].get("added_within_days") == 30
    assert "cutoff_date" in result["filters_applied"]


@pytest.mark.asyncio
async def test_added_within_days_larger_window_gte_smaller():
    """A larger time window should return >= features than a smaller one."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    small = await search_roadmap(added_within_days=7, limit=100)
    large = await search_roadmap(added_within_days=90, limit=100)

    assert large["total_found"] >= small["total_found"]


@pytest.mark.asyncio
async def test_added_within_days_clamping_low():
    """Days below 1 is clamped to 1."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(added_within_days=0)

    assert result["filters_applied"]["added_within_days"] == 1


@pytest.mark.asyncio
async def test_added_within_days_clamping_high():
    """Days above 365 is clamped to 365."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(added_within_days=9999)

    assert result["filters_applied"]["added_within_days"] == 365


@pytest.mark.asyncio
async def test_added_within_days_features_have_created_date():
    """All returned features should have a created date when filtering by recency."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(added_within_days=365, limit=100)

    for feature in result["features"]:
        assert feature["created"] is not None
        assert feature["created"] != ""


@pytest.mark.asyncio
async def test_added_within_days_combined_with_product():
    """added_within_days can be combined with other filters."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(product="Teams", added_within_days=365, limit=5)

    assert result["filters_applied"].get("product") == "Teams"
    assert result["filters_applied"].get("added_within_days") == 365
    for feature in result["features"]:
        assert any("teams" in tag.lower() for tag in feature["tags"])
        assert feature["created"] is not None


@pytest.mark.asyncio
async def test_added_within_days_none_means_no_filter():
    """When added_within_days is None, no recency filter is applied."""
    from m365_roadmap_mcp.tools.search import search_roadmap

    result = await search_roadmap(limit=5)

    assert "added_within_days" not in result["filters_applied"]
    assert "cutoff_date" not in result["filters_applied"]
