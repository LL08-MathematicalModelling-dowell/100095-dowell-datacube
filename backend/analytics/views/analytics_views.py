from datetime import datetime, timedelta, timezone
import logging

from django.conf import settings
from adrf.views import APIView as AsyncAPIView
from pymongo.errors import OperationFailure
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from analytics.services.date_range import parse_analytics_date_range
from analytics.services.inventory_stats import aggregate_db_operations, build_inventory
from analytics.services.platform_stats import (
    aggregate_file_storage,
    aggregate_http_methods,
    aggregate_http_summary,
    aggregate_metadata_counts,
    aggregate_metadata_storage_totals,
    aggregate_top_collections_scoped,
    count_slow_queries,
    file_storage_trend,
    get_usage_snapshot,
)


logger = logging.getLogger(__name__)


class AnalyticsBaseView(AsyncAPIView):
    """Base async view for analytics with MongoDB connection."""
    permission_classes = [IsAuthenticated]

    @property
    async def analytics_db(self):
        client = settings.MONGODB_CLIENT
        return client["datacube_analytics"]

    def get_user_id(self, request) -> str:
        return str(request.user.pk)

    def get_period(self, request):
        return parse_analytics_date_range(request)


class DashboardOverviewView(AnalyticsBaseView):
    """Dashboard with base + technical summaries and configurable date range."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        start, end, period = self.get_period(request)

        http = await aggregate_http_summary(user_id, start=start, end=end)
        storage_files = await aggregate_file_storage(user_id)
        storage_data = await aggregate_metadata_storage_totals(user_id)
        meta_counts = await aggregate_metadata_counts(user_id)
        usage = get_usage_snapshot(user_id)
        methods = await aggregate_http_methods(user_id, start=start, end=end)
        slow_count = await count_slow_queries(user_id, start=start, end=end)

        inventory_preview = await build_inventory(
            user_id, start, end, refresh_storage=False, skip_storage_refresh=True
        )
        inv_totals = inventory_preview.get("totals") or {}

        file_mb = round(storage_files["total_bytes"] / (1024 * 1024), 2)
        data_mb = round(storage_data["storage_data_bytes"] / (1024 * 1024), 2)

        base_summary = {
            "database_count": meta_counts["database_count"],
            "collection_count": meta_counts["collection_count"],
            "document_count": inv_totals.get("document_count", 0),
            "storage_files_mb": file_mb,
            "storage_data_mb": data_mb,
            "storage_total_mb": round(file_mb + data_mb, 2),
            "file_count": storage_files["file_count"],
            "api_calls_current_month": usage.get("api_calls_current_month", 0),
            "subscription_plan": usage.get("subscription_plan", "free"),
            "role": usage.get("role", "developer"),
            "last_activity_at": inv_totals.get("last_activity_at"),
            "api_calls_in_period": inv_totals.get("api_calls", 0),
        }

        technical_summary = {
            "total_requests": http["total_requests"],
            "avg_response_time_ms": http["avg_response_time_ms"],
            "error_rate_percent": http["error_rate_percent"],
            "slow_queries": slow_count,
        }

        overview = {
            **base_summary,
            **technical_summary,
            "slow_queries_7d": slow_count,
            "total_storage_mb": base_summary["storage_total_mb"],
        }

        return Response({
            "success": True,
            "period": period,
            "base_summary": base_summary,
            "technical_summary": technical_summary,
            "overview": overview,
            "methods": methods,
            "methods_7d": methods,
            "daily_requests": http["daily_requests"],
        })


class InventoryView(AnalyticsBaseView):
    """Per-database and per-collection inventory with trends for the selected period."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        start, end, period = self.get_period(request)
        database_id = (request.query_params.get("database_id") or "").strip() or None
        refresh = request.query_params.get("refresh_storage", "").lower() in (
            "1",
            "true",
            "yes",
        )

        payload = await build_inventory(
            user_id,
            start,
            end,
            database_id=database_id,
            refresh_storage=refresh,
        )

        return Response({
            "success": True,
            "period": period,
            **payload,
        })


class PerformanceMetricsView(AnalyticsBaseView):
    """Response time percentiles (p50, p90, p95, p99) and throughput."""

    _MAX_CLIENT_SIDE_DOCS = 100_000
    _SAMPLE_FALLBACK = 50_000

    async def _percentiles_ms_server(self, coll, user_id: str, start, end) -> dict | None:
        pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
            {
                "$group": {
                    "_id": None,
                    "n": {"$sum": 1},
                    "pct": {
                        "$percentile": {
                            "input": "$duration_ms",
                            "p": [0.5, 0.9, 0.95, 0.99],
                            "method": "approximate",
                        }
                    },
                }
            },
        ]
        try:
            cursor = await coll.aggregate(pipeline)
            rows = await cursor.to_list(length=1)
        except OperationFailure as exc:
            logger.info("Analytics percentile aggregation not available: %s", exc)
            return None
        if not rows or rows[0].get("n", 0) == 0:
            return {}
        pct = rows[0]["pct"] or []
        if len(pct) < 4:
            return None
        return {
            "p50": round(float(pct[0]), 2),
            "p90": round(float(pct[1]), 2),
            "p95": round(float(pct[2]), 2),
            "p99": round(float(pct[3]), 2),
        }

    async def _percentiles_ms_fallback(self, coll, user_id: str, start, end) -> dict:
        match = {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}
        total = await coll.count_documents(match)
        if total == 0:
            return {}

        if total <= self._MAX_CLIENT_SIDE_DOCS:
            cursor = coll.find(match, {"duration_ms": 1, "_id": 0})
            docs = await cursor.to_list(length=self._MAX_CLIENT_SIDE_DOCS + 1)
            durations_ms = [d["duration_ms"] for d in docs]
        else:
            sample_size = min(self._SAMPLE_FALLBACK, total)
            pipeline = [
                {"$match": match},
                {"$sample": {"size": sample_size}},
                {"$project": {"duration_ms": 1, "_id": 0}},
            ]
            cursor = await coll.aggregate(pipeline)
            docs = await cursor.to_list(length=sample_size)
            durations_ms = [d["duration_ms"] for d in docs]

        durations_ms.sort()
        n = len(durations_ms)

        def percentile(p: int) -> float:
            idx = int((p / 100) * n)
            return float(durations_ms[min(idx, n - 1)])

        return {
            "p50": round(percentile(50), 2),
            "p90": round(percentile(90), 2),
            "p95": round(percentile(95), 2),
            "p99": round(percentile(99), 2),
        }

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        start, end, period = self.get_period(request)

        coll = db["http_requests"]
        percentiles = await self._percentiles_ms_server(coll, user_id, start, end)
        if percentiles is None:
            percentiles = await self._percentiles_ms_fallback(coll, user_id, start, end)

        day_start = end - timedelta(days=1)
        pipeline_throughput = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": day_start, "$lte": end}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        cursor = await db["http_requests"].aggregate(pipeline_throughput)
        throughput_data = await cursor.to_list(length=100)
        throughput = [{"hour": d["_id"], "requests": d["count"]} for d in throughput_data]

        return Response({
            "success": True,
            "period": period,
            "percentiles_ms": percentiles,
            "throughput_last_24h": throughput,
        })


class ErrorAnalyticsView(AnalyticsBaseView):
    """Error breakdown by status code, endpoint, and error type."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        start, end, period = self.get_period(request)

        pipeline_status = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start, "$lte": end},
                    "status_code": {"$gte": 400},
                }
            },
            {"$group": {"_id": "$status_code", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        cursor = await db["http_requests"].aggregate(pipeline_status)
        status_errors = await cursor.to_list(length=100)
        error_by_status = {str(d["_id"]): d["count"] for d in status_errors}

        pipeline_endpoints = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start, "$lte": end},
                    "status_code": {"$gte": 400},
                }
            },
            {"$group": {"_id": "$path", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
        ]
        cursor = await db["http_requests"].aggregate(pipeline_endpoints)
        top_error_endpoints = await cursor.to_list(length=5)
        top_endpoints = [{"path": d["_id"], "errors": d["count"]} for d in top_error_endpoints]

        pipeline_types = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": "$error_type", "count": {"$sum": 1}}},
        ]
        cursor = await db["errors"].aggregate(pipeline_types)
        error_types = await cursor.to_list(length=10)
        error_type_map = {d["_id"]: d["count"] for d in error_types if d["_id"]}

        return Response({
            "success": True,
            "period": period,
            "errors_by_status_code": error_by_status,
            "top_error_endpoints": top_endpoints,
            "error_types": error_type_map,
        })


class TopCollectionsView(AnalyticsBaseView):
    """Most accessed collections (scoped by database when available)."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        start, end, period = self.get_period(request)
        collections = await aggregate_top_collections_scoped(
            user_id, start=start, end=end, limit=15
        )
        return Response({
            "success": True,
            "period": period,
            "top_collections": collections,
        })


class SlowQueriesView(AnalyticsBaseView):
    """List of recent slow queries with details (paginated)."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        start, end, period = self.get_period(request)
        limit = min(int(request.query_params.get("limit", 20)), 100)
        offset = int(request.query_params.get("offset", 0))

        query = {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}
        cursor = (
            db["slow_queries"]
            .find(query)
            .sort("timestamp", -1)
            .skip(offset)
            .limit(limit)
        )
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
        total = await db["slow_queries"].count_documents(query)
        return Response({
            "success": True,
            "period": period,
            "data": slow_queries,
            "pagination": {"total": total, "limit": limit, "offset": offset},
        })


class RequestVolumeByEndpointView(AnalyticsBaseView):
    """Bar chart data: requests count per endpoint."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        start, end, period = self.get_period(request)

        pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": "$path", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15},
        ]
        cursor = await db["http_requests"].aggregate(pipeline)
        result = await cursor.to_list(length=15)
        endpoints = [{"endpoint": d["_id"], "requests": d["count"]} for d in result]
        return Response({
            "success": True,
            "period": period,
            "endpoint_volume": endpoints,
        })


class DatabaseOperationBreakdownView(AnalyticsBaseView):
    """Pie chart data: operations by type."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        db = await self.analytics_db
        start, end, period = self.get_period(request)

        pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": "$operation_type", "count": {"$sum": 1}}},
        ]
        cursor = await db["db_operations"].aggregate(pipeline)
        result = await cursor.to_list(length=20)
        operations = {d["_id"]: d["count"] for d in result}
        return Response({
            "success": True,
            "period": period,
            "operation_breakdown": operations,
        })


class UserStorageTrendView(AnalyticsBaseView):
    """Storage usage over time: GridFS uploads + data-plane API calls trend."""

    async def get(self, request):
        user_id = self.get_user_id(request)
        start, end, period = self.get_period(request)

        file_trend = await file_storage_trend(user_id, start=start, end=end)
        ops = await aggregate_db_operations(user_id, start, end)
        data_daily: dict[str, int] = {}
        for _db_id, series in ops["daily_by_db"].items():
            for point in series:
                data_daily[point["date"]] = data_daily.get(point["date"], 0) + point[
                    "api_calls"
                ]
        data_trend = [
            {"date": d, "storage_mb": 0, "api_calls": data_daily[d], "kind": "data_activity"}
            for d in sorted(data_daily.keys())
        ]

        return Response({
            "success": True,
            "period": period,
            "storage_trend_mb": file_trend,
            "data_activity_trend": data_trend,
        })
