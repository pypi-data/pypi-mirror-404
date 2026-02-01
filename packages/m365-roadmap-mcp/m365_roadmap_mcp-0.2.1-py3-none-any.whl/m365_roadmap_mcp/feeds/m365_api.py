"""M365 Roadmap API fetching and parsing."""

import httpx

from ..models.feature import RoadmapFeature

M365_ROADMAP_API_URL = "https://www.microsoft.com/releasecommunications/api/v1/m365"


async def fetch_features() -> list[RoadmapFeature]:
    """Fetch and parse features from the M365 Roadmap API.

    Returns:
        List of RoadmapFeature objects sorted by created date (newest first).
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(M365_ROADMAP_API_URL, timeout=30.0)
        response.raise_for_status()

    items = response.json()
    features = []

    for item in items:
        feature = _parse_item(item)
        if feature:
            features.append(feature)

    # Sort by created date, newest first
    features.sort(key=lambda f: f.created or "", reverse=True)
    return features


def _parse_item(item: dict) -> RoadmapFeature | None:
    """Parse a single API item into a RoadmapFeature.

    Args:
        item: A dictionary from the API JSON array.

    Returns:
        RoadmapFeature object or None if parsing fails.
    """
    try:
        # Extract product tags from tagsContainer
        tags_container = item.get("tagsContainer") or {}
        products = [
            p["tagName"]
            for p in tags_container.get("products", [])
            if "tagName" in p
        ]

        # Extract cloud instances from tagsContainer
        cloud_instances = [
            c["tagName"]
            for c in tags_container.get("cloudInstances", [])
            if "tagName" in c
        ]

        return RoadmapFeature(
            id=str(item.get("id", "")),
            title=item.get("title", ""),
            description=item.get("description", ""),
            status=item.get("status"),
            tags=products,
            cloud_instances=cloud_instances,
            public_disclosure_date=item.get("publicDisclosureAvailabilityDate"),
            created=item.get("created"),
            modified=item.get("modified"),
        )
    except Exception:
        return None
