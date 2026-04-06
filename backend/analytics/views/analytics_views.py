from datetime import datetime, timedelta, timezone

from django.conf import settings
from adrf.views import APIView as AsyncAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class AnalyticsBaseView(AsyncAPIView):
    """Base async view for analytics with MongoDB connection."""
    permission_classes = [IsAuthenticated]

    @property
    async def analytics_db(self):
        # Create a client per request (or reuse a singleton). For simplicity, create new.
        client = settings.MONGODB_CLIENT
        return client["datacube_analytics"]

    def get_user_id(self, request) -> str:
        return str(request.user.pk)


class DashboardOverviewView(AnalyticsBaseView):
    """Main dashboard summary: total requests, avg duration, error rate, storage used."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        # 1. Total requests and avg duration
        pipeline_requests = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": None,
                "total_requests": {"$sum": 1},
                "avg_duration_ms": {"$avg": "$duration_ms"},
                "error_count": {"$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}}
            }}
        ]
        cursor = await db["http_requests"].aggregate(pipeline_requests)
        req_result = await cursor.to_list(length=1)
        total_requests = req_result[0]["total_requests"] if req_result else 0
        avg_duration = round(req_result[0]["avg_duration_ms"], 2) if req_result else 0
        error_count = req_result[0]["error_count"] if req_result else 0
        error_rate = round((error_count / total_requests) * 100, 2) if total_requests > 0 else 0

        # 2. Total storage used from file_metadata (if collection exists)
        file_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total_bytes": {"$sum": "$file_size_bytes"}}}
        ]
        cursor = await db["file_metadata"].aggregate(file_pipeline)
        file_result = await cursor.to_list(length=1)
        total_storage_mb = round((file_result[0]["total_bytes"] / (1024*1024)) if file_result else 0, 2)

        # 3. Requests per day (last 7 days)
        pipeline_daily = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_ms"}
            }},
            {"$sort": {"_id": 1}}
        ]
        cursor = await db["http_requests"].aggregate(pipeline_daily)
        daily_data = await cursor.to_list(length=100)
        dates = [d["_id"] for d in daily_data]
        counts = [d["count"] for d in daily_data]
        durations = [round(d["avg_duration"], 2) for d in daily_data]

        return Response({
            "success": True,
            "overview": {
                "total_requests": total_requests,
                "avg_response_time_ms": avg_duration,
                "error_rate_percent": error_rate,
                "total_storage_mb": total_storage_mb,
            },
            "daily_requests": {
                "dates": dates,
                "counts": counts,
                "avg_durations_ms": durations,
            }
        })


class PerformanceMetricsView(AnalyticsBaseView):
    """Response time percentiles (p50, p90, p95, p99) and throughput."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        # Get all durations for the period
        cursor = db["http_requests"].find(
            {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}},
            {"duration_ms": 1, "_id": 0}
        )
        durations = await cursor.to_list(length=None)
        durations_ms = [d["duration_ms"] for d in durations]
        durations_ms.sort()
        n = len(durations_ms)
        if n == 0:
            return Response({"success": True, "percentiles": {}})

        def percentile(p):
            idx = int((p / 100) * n)
            return durations_ms[min(idx, n-1)]

        percentiles = {
            "p50": round(percentile(50), 2),
            "p90": round(percentile(90), 2),
            "p95": round(percentile(95), 2),
            "p99": round(percentile(99), 2),
        }

        # Throughput (requests per minute over last 24h)
        day_start = end - timedelta(days=1)
        pipeline_throughput = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": day_start}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        cursor = await db["http_requests"].aggregate(pipeline_throughput)
        throughput_data = await cursor.to_list(length=100)
        throughput = [{"hour": d["_id"], "requests": d["count"]} for d in throughput_data]

        return Response({
            "success": True,
            "percentiles_ms": percentiles,
            "throughput_last_24h": throughput,
        })


class ErrorAnalyticsView(AnalyticsBaseView):
    """Error breakdown by status code, endpoint, and error type."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        # 1. Errors by status code
        pipeline_status = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start}, "status_code": {"$gte": 400}}},
            {"$group": {"_id": "$status_code", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        cursor = await db["http_requests"].aggregate(pipeline_status)
        status_errors = await cursor.to_list(length=100)
        error_by_status = {str(d["_id"]): d["count"] for d in status_errors}

        # 2. Top 5 error‑prone endpoints
        pipeline_endpoints = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start}, "status_code": {"$gte": 400}}},
            {"$group": {"_id": "$path", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        cursor = await db["http_requests"].aggregate(pipeline_endpoints)
        top_error_endpoints = await cursor.to_list(length=5)
        top_endpoints = [{"path": d["_id"], "errors": d["count"]} for d in top_error_endpoints]

        # 3. Error types from error collection
        pipeline_types = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start}}},
            {"$group": {"_id": "$error_type", "count": {"$sum": 1}}}
        ]
        cursor = await db["errors"].aggregate(pipeline_types)
        error_types = await cursor.to_list(length=10)
        error_type_map = {d["_id"]: d["count"] for d in error_types if d["_id"]}

        return Response({
            "success": True,
            "errors_by_status_code": error_by_status,
            "top_error_endpoints": top_endpoints,
            "error_types": error_type_map,
        })


class TopCollectionsView(AnalyticsBaseView):
    """Most accessed collections (by operations count)."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start}}},
            {"$group": {"_id": "$collection", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        cursor = await db["db_operations"].aggregate(pipeline)
        top = await cursor.to_list(length=10)
        collections = [{"name": d["_id"], "operations": d["count"]} for d in top]
        return Response({"success": True, "top_collections": collections})


class SlowQueriesView(AnalyticsBaseView):
    """List of recent slow queries with details (paginated)."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        limit = int(request.query_params.get("limit", 20))
        offset = int(request.query_params.get("offset", 0))

        cursor = db["slow_queries"].find(
            {"user_id": user_id}
        ).sort("timestamp", -1).skip(offset).limit(limit)
        slow_queries = []
        async for doc in cursor:
            slow_queries.append({
                "id": str(doc["_id"]),
                "duration_ms": doc["duration_ms"],
                "threshold_ms": doc["threshold_ms"],
                "collection": doc["collection"],
                "db_id": doc.get("db_id"),
                "query_details": doc.get("query_details", {}),
                "timestamp": doc["timestamp"].isoformat(),
            })
        total = await db["slow_queries"].count_documents({"user_id": user_id})
        return Response({
            "success": True,
            "data": slow_queries,
            "pagination": {"total": total, "limit": limit, "offset": offset}
        })


class RequestVolumeByEndpointView(AnalyticsBaseView):
    """Bar chart data: requests count per endpoint (last 7 days)."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start}}},
            {"$group": {"_id": "$path", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]
        cursor = await db["http_requests"].aggregate(pipeline)
        result = await cursor.to_list(length=15)
        endpoints = [{"endpoint": d["_id"], "requests": d["count"]} for d in result]
        return Response({"success": True, "endpoint_volume": endpoints})


class DatabaseOperationBreakdownView(AnalyticsBaseView):
    """Pie chart data: operations by type (insert, query, update, delete, etc.)."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start}}},
            {"$group": {"_id": "$operation_type", "count": {"$sum": 1}}}
        ]
        cursor = await db["db_operations"].aggregate(pipeline)
        result = await cursor.to_list(length=20)
        operations = {d["_id"]: d["count"] for d in result}
        return Response({"success": True, "operation_breakdown": operations})


class UserStorageTrendView(AnalyticsBaseView):
    """Storage usage over time (daily snapshot from file_metadata)."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)

        # Use file_metadata with upload_date field
        pipeline = [
            {"$match": {"user_id": user_id, "upload_date": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$upload_date"}},
                "total_bytes": {"$sum": "$file_size_bytes"}
            }},
            {"$sort": {"_id": 1}}
        ]
        cursor = await db["file_metadata"].aggregate(pipeline)
        result = await cursor.to_list(length=100)
        trend = [{"date": d["_id"], "storage_mb": round(d["total_bytes"] / (1024*1024), 2)} for d in result]
        return Response({"success": True, "storage_trend_mb": trend})
