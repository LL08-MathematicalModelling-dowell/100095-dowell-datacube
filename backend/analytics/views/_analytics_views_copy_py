import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas

from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.views.base import BaseAPIView
from api.utils.mongodb import jsonify_object_ids
from analytics.services.analytics_services import AnalyticsService
from ..serializers import (
    SummarySerializer, TimeSeriesSerializer, 
    SlowQuerySerializer, ExportSerializer
)

class DashboardSummaryView(BaseAPIView):
    """
    Primary landing view for the Datacube Analytics Dashboard.
    Provides a consolidated 'Pulse' of the database/collection.
    """
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    async def get(self, request):
        db_id = request.query_params.get('database_id')
        days = int(request.query_params.get('days', 7))
        
        if not db_id:
            return Response({"error": "database_id is required"}, status=400)

        svc = AnalyticsService(user_id=str(request.user.pk))
        
        # 1. Fetch Storage Snapshot (from latest Celery task)
        storage = await svc.get_storage_stats(db_id)
        
        # 2. Fetch Chart Data (Historical Summaries + Live Hourly)
        charts = await svc.get_dashboard_charts(db_id, days=days)
        
        return Response({
            "success": True,
            "tenant_id": request.user.id,
            "db_id": db_id,
            "summary": storage,
            "charts": charts
        })

class SlowQueryLogView(BaseAPIView):
    """Fetches high-latency queries for performance tuning."""
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    async def get(self, request):
        svc = AnalyticsService(user_id=str(request.user.pk))
        
        # Query raw activity logs where type is 'slow_query'
        # Using the standard time-series collection 'user_activity'
        limit = int(request.query_params.get('limit', 20))
        
        cursor = svc.activity.find({
            "metadata.user_id": svc.user_id,
            "metadata.type": "slow_query"
        }).sort("timestamp", -1).limit(limit)
        
        queries = await cursor.to_list(length=limit)
        return Response({
            "success": True,
            "results": jsonify_object_ids(queries)
        })

class DataExportView(BaseAPIView):
    """
    Generates CSV/PDF reports for business compliance.
    Utilizes Pandas for CSV generation and ReportLab for PDF.
    """
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    async def get(self, request):
        params = self.validate_serializer(ExportSerializer, request.query_params)
        data_type = params['data_type']
        file_format = params['format']

        svc = AnalyticsService(user_id=str(request.user.pk))
        
        # 1. Fetch data based on type
        if data_type == 'storage_history':
            cursor = svc.storage_history.find({"user_id": svc.user_id}).limit(100)
            data = await cursor.to_list(length=100)
        else:
            # Fallback to daily summaries
            cursor = svc.summaries.find({"user_id": svc.user_id}).limit(100)
            data = await cursor.to_list(length=100)

        # 2. Handle Export Format
        if file_format == 'csv':
            df = pd.DataFrame(jsonify_object_ids(data))
            output = BytesIO()
            df.to_csv(output, index=False)
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="datacube_{data_type}.csv"'
            return response

        elif file_format == 'pdf':
            output = BytesIO()
            p = canvas.Canvas(output)
            p.drawString(100, 800, f"Datacube Analytics Report: {data_type}")
            p.drawString(100, 780, f"Generated for User: {request.user.email}")
            
            # Simple PDF Table Simulation
            y = 750
            for item in data[:20]:
                p.drawString(100, y, f"Date: {item.get('timestamp') or item.get('date')} - Value: {item.get('total_size') or item.get('total_ops')}")
                y -= 20
            
            p.save()
            response = HttpResponse(output.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="datacube_report.pdf"'
            return response
