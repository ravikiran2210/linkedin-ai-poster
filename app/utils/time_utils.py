"""Time and date helpers."""

from __future__ import annotations

import datetime as dt


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def hours_ago(hours: int) -> dt.datetime:
    return utc_now() - dt.timedelta(hours=hours)


def age_hours(published: dt.datetime | None) -> float:
    """Return how many hours old an item is. Default to 72h if unknown."""
    if published is None:
        return 72.0
    now = utc_now()
    if published.tzinfo is None:
        published = published.replace(tzinfo=dt.UTC)
    delta = now - published
    return max(delta.total_seconds() / 3600, 0.0)
