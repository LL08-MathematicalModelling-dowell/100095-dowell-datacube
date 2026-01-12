"""
URL configuration for the Datacube 'analytics' app.
Supports optional trailing slashes for production resilience.
"""

from django.urls import re_path
from analytics.views.analytics_views import (
    DashboardSummaryView,
    SlowQueryLogView,
    DataExportView,
)

app_name = 'analytics'

urlpatterns = [
    # Consolidated Dashboard (Combines summary, time-series, and usage)
    re_path(r"^dashboard/?$", DashboardSummaryView.as_view(), name='dashboard'),

    # Deep-dive Performance logs
    re_path(r"^slow-queries/?$", SlowQueryLogView.as_view(), name='slow_queries'),

    # File Generation (CSV/PDF)
    re_path(r"^export/?$", DataExportView.as_view(), name='export'),
]
