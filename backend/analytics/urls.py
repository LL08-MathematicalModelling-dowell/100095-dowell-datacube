from django.urls import path, re_path

from analytics.views.analytics_views import (
    DashboardOverviewView,
    PerformanceMetricsView,
    ErrorAnalyticsView,
    TopCollectionsView,
    SlowQueriesView,
    RequestVolumeByEndpointView,
    DatabaseOperationBreakdownView,
    UserStorageTrendView,
)


app_name = "analytics"

urlpatterns = [
    re_path(r'^dashboard/?$', DashboardOverviewView.as_view(), name='analytics-dashboard'),
    re_path(r'^performance/?$', PerformanceMetricsView.as_view(), name='analytics-performance'),
    re_path(r'^errors/?$', ErrorAnalyticsView.as_view(), name='analytics-errors'),
    re_path(r'^top-collections/?$', TopCollectionsView.as_view(), name='analytics-top-collections'),
    re_path(r'^slow-queries/?$', SlowQueriesView.as_view(), name='analytics-slow-queries'),
    re_path(r'^endpoint-volume/?$', RequestVolumeByEndpointView.as_view(), name='analytics-endpoint-volume'),
    re_path(r'^operation-breakdown/?$', DatabaseOperationBreakdownView.as_view(), name='analytics-operation-breakdown'),
    re_path(r'^storage-trend/?$', UserStorageTrendView.as_view(), name='analytics-storage-trend'),
]