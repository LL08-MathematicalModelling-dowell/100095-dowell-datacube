import logging
from datetime import datetime, timedelta, timezone
from django.conf import settings
from api.utils.mongodb import get_async_client, jsonify_object_ids

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        # Use the global client to prevent connection exhaustion
        self.client = get_async_client()
        
        # Dedicated Ops Database
        self.ops_db = self.client['platform_ops']
        
        # Optimized Collections
        self.activity = self.ops_db['user_activity']      # Time Series
        self.storage_history = self.ops_db['storage_snapshots']
        self.summaries = self.ops_db['daily_summaries']  # Aggregated for Frontend

    # --- LOGGING (Called by Tasks/Middleware) ---

    async def log_usage(self, action: str, details: dict):
        """Logs general API navigation/usage."""
        await self.activity.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "metadata": {"user_id": self.user_id, "type": "usage"},
            "action": action,
            "details": details
        })

    async def log_io(self, io_type: str, collection: str, duration_ms: float, success: bool):
        """Logs Read/Write performance and success rates."""
        await self.activity.insert_one({
            "timestamp": datetime.utcnow(),
            "metadata": {"user_id": self.user_id, "type": "io", "coll": collection},
            "io_type": io_type,
            "latency": duration_ms,
            "success": success
        })

    async def log_slow_query(self, query: dict, duration_ms: float):
        """Logs queries exceeding the Datacube threshold."""
        await self.activity.insert_one({
            "timestamp": datetime.utcnow(),
            "metadata": {"user_id": self.user_id, "type": "slow_query"},
            "query_preview": str(query)[:500],
            "duration": duration_ms
        })

    async def collect_time_series_metrics(self, db_id: str, metrics: dict):
        """Snapshots DB health metrics from a background task."""
        await self.storage_history.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "user_id": self.user_id,
            "db_id": db_id,
            **metrics # doc_count, size_mb, etc.
        })

    # --- AGGREGATION ENGINE (The 2026 Secret Sauce) ---

    async def run_daily_compaction(self, target_date: datetime):
        """
        Aggregates raw logs into a single summary row for this tenant.
        Ensures frontend charts don't have to process millions of rows.
        """
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lt": end},
                "metadata.user_id": self.user_id
            }},
            {"$group": {
                "_id": "$metadata.user_id",
                "total_ops": {"$sum": 1},
                "avg_latency": {"$avg": "$latency"},
                "error_count": {"$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}}
            }}
        ]
        
        async for result in self.activity.aggregate(pipeline):
            await self.summaries.update_one(
                {"date": start, "user_id": self.user_id},
                {"$set": result},
                upsert=True
            )

    # --- DATA RETRIEVAL (For Frontend Dashboards) ---

    async def get_dashboard_charts(self, db_id: str, days: int = 7):
        """
        Returns data formatted for Recharts/Chart.js.
        Queries Summaries first (fast), then Raw for today (accurate).
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # 1. Get historical daily summaries
        summaries = await self.summaries.find({
            "user_id": self.user_id,
            "date": {"$gte": cutoff}
        }).sort("date", 1).to_list(100)

        # 2. Get today's hourly trend from raw activity
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        raw_pipeline = [
            {"$match": {
                "timestamp": {"$gte": today_start},
                "metadata.user_id": self.user_id
            }},
            {"$group": {
                "_id": {"$hour": "$timestamp"},
                "ops": {"$sum": 1},
                "latency": {"$avg": "$latency"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        today_trend = await self.activity.aggregate(raw_pipeline).to_list(24)

        return {
            "historical": jsonify_object_ids(summaries),
            "today_hourly": today_trend
        }

    async def get_storage_stats(self, db_id: str):
        """Returns latest storage metrics for Quota enforcement and UI."""
        latest = await self.storage_history.find_one(
            {"user_id": self.user_id, "db_id": db_id},
            sort=[("timestamp", -1)]
        )
        return jsonify_object_ids(latest) if latest else {}
