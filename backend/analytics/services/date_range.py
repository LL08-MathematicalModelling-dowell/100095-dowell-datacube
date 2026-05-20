"""Parse analytics date filters from query parameters."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from rest_framework.request import Request


DEFAULT_ANALYTICS_DAYS = 14
MAX_ANALYTICS_DAYS = 90


def _parse_date_param(value: str) -> datetime:
    """YYYY-MM-DD → UTC start of day."""
    d = date.fromisoformat(value.strip()[:10])
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def parse_analytics_date_range(request: Request) -> tuple[datetime, datetime, dict[str, Any]]:
    """
    Resolve [start, end] for analytics queries.

    Query params (priority):
      - start_date + end_date (YYYY-MM-DD, inclusive end day)
      - days (integer, default 14, max 90)
    """
    end = datetime.now(timezone.utc)
    start_s = (request.query_params.get("start_date") or "").strip()
    end_s = (request.query_params.get("end_date") or "").strip()

    if start_s and end_s:
        start = _parse_date_param(start_s)
        end_day = _parse_date_param(end_s)
        end = end_day + timedelta(days=1) - timedelta(microseconds=1)
    else:
        raw_days = request.query_params.get("days", str(DEFAULT_ANALYTICS_DAYS))
        try:
            days = int(raw_days)
        except (TypeError, ValueError):
            days = DEFAULT_ANALYTICS_DAYS
        days = max(1, min(days, MAX_ANALYTICS_DAYS))
        start = end - timedelta(days=days)

    if start > end:
        start, end = end, start

    span_days = max(1, (end.date() - start.date()).days + 1)
    if span_days > MAX_ANALYTICS_DAYS:
        start = end - timedelta(days=MAX_ANALYTICS_DAYS)

    period = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": (end.date() - start.date()).days + 1,
    }
    return start, end, period
