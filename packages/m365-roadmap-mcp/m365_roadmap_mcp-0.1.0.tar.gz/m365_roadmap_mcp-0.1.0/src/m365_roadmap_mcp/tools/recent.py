"""Tool for listing recently added M365 Roadmap features."""

from datetime import datetime, timedelta, timezone

from ..feeds.m365_api import fetch_features


async def list_recent_additions(days: int = 7) -> dict:
    """List features recently added to the Microsoft 365 Roadmap.

    Use this tool to monitor what new features have appeared on the roadmap
    within a given time window. Useful for staying current on Microsoft's
    latest plans and announcements.

    Args:
        days: Number of days to look back (default: 7, clamped to 1–365).

    Returns:
        Dictionary with:
        - total_found: Number of features added within the time window
        - features: List of recently added feature objects
        - days_queried: The actual number of days used (after clamping)
        - cutoff_date: The earliest date included in the results (ISO format)
    """
    # Clamp days to reasonable bounds
    days = max(1, min(days, 365))

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    features = await fetch_features()

    recent = []
    for feature in features:
        if not feature.created:
            continue
        try:
            created_dt = datetime.fromisoformat(feature.created)
            # Ensure timezone-aware comparison
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            if created_dt >= cutoff:
                recent.append(feature)
        except (ValueError, TypeError):
            continue

    return {
        "total_found": len(recent),
        "features": [f.to_dict() for f in recent],
        "days_queried": days,
        "cutoff_date": cutoff.isoformat(),
    }
