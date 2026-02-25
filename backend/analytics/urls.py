"""
URL configuration for the Datacube 'analytics' app.
Supports optional trailing slashes for production resilience.
"""

from django.urls import re_path
from analytics.views.analytics_views_copy import (
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


from django.urls import path
from analytics.views.analytics_views import AnalyticsDashboardView, AnalyticsStorageView, AnalyticsSlowQueriesView

urlpatterns = [
    # ... other paths
    path('analytics/dashboard/', AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    path('analytics/storage/', AnalyticsStorageView.as_view(), name='analytics-storage'),
    path('analytics/slow-queries/', AnalyticsSlowQueriesView.as_view(), name='analytics-slow-queries'),
]
