from datetime import datetime, timezone

from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.http import HttpResponse

from api.views.base import BaseAPIView
from analytics.analytics_serializers import ExportQuerySerializer
from analytics.services.analytics_services import AnalyticsService
from analytics.utils.pdf_generator import generate_pdf_report

from api.views.base import BaseAPIView
from analytics.analytics_serializers import (
    DashboardQuerySerializer,
    StorageQuerySerializer,
)


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
        print("Received request for dashboard analytics with params:", request.query_params)
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
    

class AnalyticsExportView(BaseAPIView):
    """
    GET /api/analytics/export/?db_id=<id>&days=30&format=pdf
    Returns a downloadable PDF report.
    """
    permission_classes = [IsAuthenticated]

    @property
    def analytics_svc(self):
        return AnalyticsService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        # Validate parameters
        params = self.validate_serializer(ExportQuerySerializer, request.query_params)
        db_id = params["db_id"]
        days = params["days"]
        export_format = params["format"]

        # Fetch data needed for report
        dashboard_data = await sync_to_async(self.analytics_svc.get_dashboard_charts)(
            db_id=db_id, days=days
        )
        storage_stats = await sync_to_async(self.analytics_svc.get_storage_stats)(
            db_id=db_id
        )

        # Combine data
        report_data = {
            **dashboard_data,
            "storage": storage_stats
        }

        if export_format == "pdf":
            # Generate PDF (sync function, but run in thread via sync_to_async)
            pdf_bytes = await sync_to_async(generate_pdf_report)(
                data=report_data, db_id=db_id, days=days
            )
            # Return as downloadable file
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"analytics_report_{db_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            # Should not happen due to serializer choice, but handle gracefully
            return Response(
                {"success": False, "message": f"Unsupported format: {export_format}"},
                status=status.HTTP_400_BAD_REQUEST
            )
