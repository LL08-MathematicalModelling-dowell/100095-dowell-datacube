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
from django.urls import path
from analytics.views.analytics_views import (
    AnalyticsDashboardView, AnalyticsExportView, 
    AnalyticsStorageView, AnalyticsSlowQueriesView,
)


app_name = 'analytics'

urlpatterns = [
    # Consolidated Dashboard (Combines summary, time-series, and usage)
    # re_path(r"^dashboard/?$", DashboardSummaryView.as_view(), name='dashboard'),

    # Deep-dive Performance logs
    # re_path(r"^slow-queries/?$", SlowQueryLogView.as_view(), name='slow_queries'),

    # File Generation (CSV/PDF)
    # re_path(r"^export/?$", DataExportView.as_view(), name='export'),

    # path('analytics/dashboard/'
    re_path(r"^dashboard/?$", AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    re_path(r"^storage/?$", AnalyticsStorageView.as_view(), name='analytics-storage'),
    re_path(r"^slow-queries/?$", AnalyticsSlowQueriesView.as_view(), name='analytics-slow-queries'),
    re_path(r"^export/?$", AnalyticsExportView.as_view(), name='analytics-export'),
]
