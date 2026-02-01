"""Search tool for querying and filtering M365 Roadmap features."""

from datetime import datetime, timedelta, timezone

from ..feeds.m365_api import fetch_features


async def search_roadmap(
    query: str | None = None,
    product: str | None = None,
    status: str | None = None,
    cloud_instance: str | None = None,
    feature_id: str | None = None,
    added_within_days: int | None = None,
    limit: int = 10,
) -> dict:
    """Search the Microsoft 365 Roadmap for features matching keywords and filters.

    Combines keyword search, product filtering, status filtering, cloud instance
    filtering, and recency filtering into a single flexible tool. All filter
    parameters are optional and can be combined. When no filters are provided,
    returns the most recent features.

    Use this tool to:
    - Browse recent roadmap features (no filters)
    - Search for features by keyword (query="Copilot")
    - Filter by product (product="Microsoft Teams")
    - Find features by status (status="In development", "Rolling out", "Launched")
    - Filter by cloud instance (cloud_instance="GCC High", "DoD", "GCC")
    - Retrieve a specific feature by ID (feature_id="534606")
    - List recently added features (added_within_days=30)
    - Combine any of the above (query="Copilot" + product="Teams" + cloud_instance="GCC")

    Args:
        query: Optional keyword to match against title and description (case-insensitive).
        product: Optional product tag to filter by (case-insensitive partial match,
            e.g. "Teams" matches "Microsoft Teams").
        status: Optional status filter. Valid values: In development, Rolling out, Launched.
        cloud_instance: Optional cloud instance filter (case-insensitive partial match,
            e.g. "GCC" matches "GCC", "GCC High" matches "GCC High").
        feature_id: Optional roadmap ID to retrieve a single specific feature.
            When provided, all other filters are ignored.
        added_within_days: Optional number of days to look back for recently added
            features (clamped to 1–365). Only features with a created date within
            this window are returned.
        limit: Maximum number of results to return (default: 10, max: 100).
            Ignored when feature_id is provided.

    Returns:
        Dictionary with:
        - total_found: Number of features matching the filters (before applying limit)
        - features: List of matching feature objects (up to limit)
        - filters_applied: Summary of which filters were used
    """
    features = await fetch_features()

    # Feature ID lookup is a fast path that ignores all other filters
    if feature_id:
        for feature in features:
            if feature.id == feature_id:
                return {
                    "total_found": 1,
                    "features": [feature.to_dict()],
                    "filters_applied": {"feature_id": feature_id},
                }
        return {
            "total_found": 0,
            "features": [],
            "filters_applied": {"feature_id": feature_id},
        }

    # Clamp limit to reasonable bounds
    limit = max(1, min(limit, 100))

    # Compute recency cutoff if requested
    cutoff = None
    if added_within_days is not None:
        added_within_days = max(1, min(added_within_days, 365))
        cutoff = datetime.now(timezone.utc) - timedelta(days=added_within_days)

    # Prepare lowercase values for case-insensitive matching
    query_lower = query.lower() if query else None
    product_lower = product.lower() if product else None
    status_lower = status.lower() if status else None
    cloud_lower = cloud_instance.lower() if cloud_instance else None

    # Apply all filters
    matched = []
    for feature in features:
        # Status filter
        if status_lower:
            if not feature.status or feature.status.lower() != status_lower:
                continue

        # Product filter (partial match)
        if product_lower:
            if not any(product_lower in tag.lower() for tag in feature.tags):
                continue

        # Cloud instance filter (partial match)
        if cloud_lower:
            if not any(cloud_lower in ci.lower() for ci in feature.cloud_instances):
                continue

        # Keyword search (title + description)
        if query_lower:
            if (
                query_lower not in feature.title.lower()
                and query_lower not in feature.description.lower()
            ):
                continue

        # Recency filter (added_within_days)
        if cutoff is not None:
            if not feature.created:
                continue
            try:
                created_dt = datetime.fromisoformat(feature.created)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                if created_dt < cutoff:
                    continue
            except (ValueError, TypeError):
                continue

        matched.append(feature)

    # Build filters summary
    filters_applied: dict = {}
    if query:
        filters_applied["query"] = query
    if product:
        filters_applied["product"] = product
    if status:
        filters_applied["status"] = status
    if cloud_instance:
        filters_applied["cloud_instance"] = cloud_instance
    if added_within_days is not None:
        filters_applied["added_within_days"] = added_within_days
        filters_applied["cutoff_date"] = cutoff.isoformat()
    if not filters_applied:
        filters_applied["note"] = "No filters applied, returning most recent features"

    return {
        "total_found": len(matched),
        "features": [f.to_dict() for f in matched[:limit]],
        "filters_applied": filters_applied,
    }
