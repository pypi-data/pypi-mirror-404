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
# get_feature_details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_feature_details_found():
    """Returns full details for a valid feature ID."""
    from m365_roadmap_mcp.tools.details import get_feature_details
    from m365_roadmap_mcp.tools.search import search_roadmap

    # Get a valid ID from search
    recent = await search_roadmap(limit=1)
    assert recent["features"], "Need at least one feature to test"
    fid = recent["features"][0]["id"]

    result = await get_feature_details(fid)

    assert result["found"] is True
    assert result["feature"] is not None
    assert result["feature"]["id"] == fid
    assert "error" not in result


@pytest.mark.asyncio
async def test_get_feature_details_not_found():
    """Returns found=False for a nonexistent feature ID."""
    from m365_roadmap_mcp.tools.details import get_feature_details

    result = await get_feature_details("nonexistent-id-99999")

    assert result["found"] is False
    assert result["feature"] is None
    assert "error" in result


@pytest.mark.asyncio
async def test_get_feature_details_output_structure():
    """Output contains expected keys and types."""
    from m365_roadmap_mcp.tools.details import get_feature_details
    from m365_roadmap_mcp.tools.search import search_roadmap

    recent = await search_roadmap(limit=1)
    assert recent["features"], "Need at least one feature to test"
    fid = recent["features"][0]["id"]

    result = await get_feature_details(fid)

    assert isinstance(result["found"], bool)
    assert isinstance(result["feature"], dict)
    feature = result["feature"]
    for key in ("id", "title", "description", "status", "tags",
                "cloud_instances", "public_disclosure_date", "created", "modified"):
        assert key in feature


# ---------------------------------------------------------------------------
# check_cloud_availability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_cloud_worldwide_available():
    """A feature with Worldwide instance should report available for 'Worldwide'."""
    from m365_roadmap_mcp.tools.search import search_roadmap
    from m365_roadmap_mcp.tools.cloud import check_cloud_availability

    # Find a feature that has Worldwide cloud instance
    result = await search_roadmap(cloud_instance="Worldwide", limit=1)
    assert result["features"], "Need a Worldwide feature to test"
    fid = result["features"][0]["id"]

    cloud = await check_cloud_availability(fid, "Worldwide")

    assert cloud["found"] is True
    assert cloud["available"] is True
    assert len(cloud["matched_instances"]) > 0


@pytest.mark.asyncio
async def test_check_cloud_not_available():
    """A feature without DoD should report not available for 'DoD'."""
    from m365_roadmap_mcp.tools.search import search_roadmap
    from m365_roadmap_mcp.tools.cloud import check_cloud_availability

    # Find a feature with only Worldwide (no DoD)
    result = await search_roadmap(cloud_instance="Worldwide", limit=20)
    target_id = None
    for feat in result["features"]:
        if not any("dod" in ci.lower() for ci in feat["cloud_instances"]):
            target_id = feat["id"]
            break

    if target_id is None:
        pytest.skip("Could not find a feature without DoD availability")

    cloud = await check_cloud_availability(target_id, "DoD")

    assert cloud["found"] is True
    assert cloud["available"] is False
    assert cloud["matched_instances"] == []
    assert len(cloud["all_instances"]) > 0


@pytest.mark.asyncio
async def test_check_cloud_feature_not_found():
    """Returns found=False for nonexistent feature ID."""
    from m365_roadmap_mcp.tools.cloud import check_cloud_availability

    result = await check_cloud_availability("nonexistent-id-99999", "GCC")

    assert result["found"] is False
    assert result["available"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_check_cloud_case_insensitive():
    """Cloud instance matching is case-insensitive."""
    from m365_roadmap_mcp.tools.search import search_roadmap
    from m365_roadmap_mcp.tools.cloud import check_cloud_availability

    result = await search_roadmap(cloud_instance="Worldwide", limit=1)
    assert result["features"], "Need a Worldwide feature to test"
    fid = result["features"][0]["id"]

    cloud = await check_cloud_availability(fid, "worldwide")

    assert cloud["available"] is True
    assert len(cloud["matched_instances"]) > 0


@pytest.mark.asyncio
async def test_check_cloud_output_structure():
    """Output contains all expected keys."""
    from m365_roadmap_mcp.tools.search import search_roadmap
    from m365_roadmap_mcp.tools.cloud import check_cloud_availability

    recent = await search_roadmap(limit=1)
    assert recent["features"], "Need at least one feature to test"
    fid = recent["features"][0]["id"]

    result = await check_cloud_availability(fid, "Worldwide")

    for key in ("feature_id", "instance_queried", "found", "available",
                "matched_instances", "all_instances", "status",
                "public_disclosure_date", "title"):
        assert key in result
    assert isinstance(result["available"], bool)
    assert isinstance(result["matched_instances"], list)
    assert isinstance(result["all_instances"], list)


# ---------------------------------------------------------------------------
# list_recent_additions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recent_default_7_days():
    """Default call uses 7-day window."""
    from m365_roadmap_mcp.tools.recent import list_recent_additions

    result = await list_recent_additions()

    assert result["days_queried"] == 7
    assert isinstance(result["total_found"], int)
    assert isinstance(result["features"], list)
    assert "cutoff_date" in result


@pytest.mark.asyncio
async def test_recent_custom_days():
    """Custom days parameter is respected."""
    from m365_roadmap_mcp.tools.recent import list_recent_additions

    result = await list_recent_additions(days=30)

    assert result["days_queried"] == 30


@pytest.mark.asyncio
async def test_recent_larger_window_gte_smaller():
    """A larger time window should return >= features than a smaller one."""
    from m365_roadmap_mcp.tools.recent import list_recent_additions

    small = await list_recent_additions(days=7)
    large = await list_recent_additions(days=90)

    assert large["total_found"] >= small["total_found"]


@pytest.mark.asyncio
async def test_recent_days_clamping_low():
    """Days below 1 is clamped to 1."""
    from m365_roadmap_mcp.tools.recent import list_recent_additions

    result = await list_recent_additions(days=0)

    assert result["days_queried"] == 1


@pytest.mark.asyncio
async def test_recent_days_clamping_high():
    """Days above 365 is clamped to 365."""
    from m365_roadmap_mcp.tools.recent import list_recent_additions

    result = await list_recent_additions(days=9999)

    assert result["days_queried"] == 365


@pytest.mark.asyncio
async def test_recent_features_have_created_date():
    """All returned features should have a created date."""
    from m365_roadmap_mcp.tools.recent import list_recent_additions

    result = await list_recent_additions(days=365)

    for feature in result["features"]:
        assert feature["created"] is not None
        assert feature["created"] != ""


@pytest.mark.asyncio
async def test_recent_output_structure():
    """Output contains all expected keys and types."""
    from m365_roadmap_mcp.tools.recent import list_recent_additions

    result = await list_recent_additions()

    assert "total_found" in result
    assert "features" in result
    assert "days_queried" in result
    assert "cutoff_date" in result
    assert isinstance(result["total_found"], int)
    assert isinstance(result["features"], list)
    assert isinstance(result["days_queried"], int)
    assert isinstance(result["cutoff_date"], str)
