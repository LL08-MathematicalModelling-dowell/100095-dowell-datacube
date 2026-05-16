"""Lightweight checks that analytics URL names resolve (synced with analytics/urls.py)."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_analytics_named_routes_resolve():
    names = [
        "analytics-dashboard",
        "analytics-performance",
        "analytics-errors",
        "analytics-top-collections",
        "analytics-slow-queries",
        "analytics-endpoint-volume",
        "analytics-operation-breakdown",
        "analytics-storage-trend",
    ]
    for name in names:
        url = reverse(f"analytics:{name}")
        assert url.startswith("/")
