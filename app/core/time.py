"""Time helpers shared by ORM models and services."""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    """Return a UTC timestamp suitable for MySQL DATETIME columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
