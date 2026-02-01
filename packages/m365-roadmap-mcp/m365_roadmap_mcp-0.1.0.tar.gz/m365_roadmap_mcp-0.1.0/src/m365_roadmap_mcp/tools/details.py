"""Tool for retrieving full details of a single M365 Roadmap feature."""

from ..feeds.m365_api import fetch_features


async def get_feature_details(feature_id: str) -> dict:
    """Retrieve full metadata for a specific Microsoft 365 Roadmap feature by its ID.

    Use this tool when you need complete details about a known roadmap feature,
    including its description, status, product tags, cloud instance availability,
    and release date.

    Args:
        feature_id: The unique Roadmap ID (e.g., "534606").

    Returns:
        Dictionary with:
        - found: Whether the feature was found
        - feature: Full feature object if found, None otherwise
        - error: Error message if not found
    """
    features = await fetch_features()

    for feature in features:
        if feature.id == feature_id:
            return {
                "found": True,
                "feature": feature.to_dict(),
            }

    return {
        "found": False,
        "feature": None,
        "error": f"No feature found with ID '{feature_id}'",
    }
