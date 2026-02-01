"""Tool for checking cloud instance availability of M365 Roadmap features."""

from ..feeds.m365_api import fetch_features


async def check_cloud_availability(feature_id: str, instance: str) -> dict:
    """Check whether a Microsoft 365 Roadmap feature is available for a specific cloud instance.

    Critical for government and defense clients who need to verify feature availability
    on GCC, GCC High, or DoD cloud instances before planning deployments.

    Args:
        feature_id: The unique Roadmap ID (e.g., "534606").
        instance: The cloud instance to check (e.g., "GCC", "GCC High", "DoD",
            "Worldwide"). Case-insensitive partial match is used, so "gcc" matches
            "GCC" and "GCC High".

    Returns:
        Dictionary with:
        - feature_id: The queried feature ID
        - instance_queried: The cloud instance that was checked
        - found: Whether the feature was found in the roadmap
        - available: Whether the feature is available for the queried instance
        - matched_instances: List of cloud instances that matched the query
        - all_instances: All cloud instances the feature supports
        - status: Feature status (if found)
        - public_disclosure_date: Estimated release date (if found)
        - title: Feature title (if found)
        - error: Error message (if feature not found)
    """
    features = await fetch_features()

    # Find the feature by ID
    target = None
    for feature in features:
        if feature.id == feature_id:
            target = feature
            break

    if target is None:
        return {
            "feature_id": feature_id,
            "instance_queried": instance,
            "found": False,
            "available": False,
            "matched_instances": [],
            "all_instances": [],
            "status": None,
            "public_disclosure_date": None,
            "title": None,
            "error": f"No feature found with ID '{feature_id}'",
        }

    # Case-insensitive partial match on cloud instances
    instance_lower = instance.lower()
    matched = [
        ci for ci in target.cloud_instances if instance_lower in ci.lower()
    ]

    return {
        "feature_id": feature_id,
        "instance_queried": instance,
        "found": True,
        "available": len(matched) > 0,
        "matched_instances": matched,
        "all_instances": target.cloud_instances,
        "status": target.status,
        "public_disclosure_date": target.public_disclosure_date,
        "title": target.title,
    }
