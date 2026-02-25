from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.views.base import BaseAPIView
from analytics.analytics_serializers import (
    DashboardQuerySerializer,
    StorageQuerySerializer,
)
from analytics.services.analytics_services import AnalyticsService


class AnalyticsDashboardView(BaseAPIView):
    """
    GET /api/analytics/dashboard/?db_id=<id>&days=7
    Returns dashboard charts: historical daily summaries + today's hourly trend.
    """
    permission_classes = [IsAuthenticated]

    @property
    def analytics_svc(self):
        # Instantiate service with current user
        return AnalyticsService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        # Validate query parameters
        params = self.validate_serializer(DashboardQuerySerializer, request.query_params)
        db_id = params["db_id"]
        days = params["days"]

        # Call the sync service method in a thread
        charts = await sync_to_async(self.analytics_svc.get_dashboard_charts)(
            db_id=db_id, days=days
        )

        return Response({
            "success": True,
            "data": charts
        }, status=status.HTTP_200_OK)


class AnalyticsStorageView(BaseAPIView):
    """
    GET /api/analytics/storage/?db_id=<id>
    Returns the latest storage snapshot for the database.
    """
    permission_classes = [IsAuthenticated]

    @property
    def analytics_svc(self):
        return AnalyticsService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        params = self.validate_serializer(StorageQuerySerializer, request.query_params)
        db_id = params["db_id"]

        stats = await sync_to_async(self.analytics_svc.get_storage_stats)(db_id=db_id)

        return Response({
            "success": True,
            "data": stats
        }, status=status.HTTP_200_OK)
    

class AnalyticsSlowQueriesView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @property
    def analytics_svc(self):
        return AnalyticsService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        db_id = request.query_params.get("db_id")
        limit = int(request.query_params.get("limit", 20))
        # Assuming we add get_slow_queries method to AnalyticsService
        slow_queries = await sync_to_async(self.analytics_svc.get_slow_queries)(
            db_id=db_id, limit=limit
        )
        return Response({"success": True, "data": slow_queries})