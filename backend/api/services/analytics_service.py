from datetime import datetime, timedelta, timezone
from django.conf import settings


# api/services/analytics_service.py
class AnalyticsService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.db = settings.MONGODB_CLIENT["platform_ops"]

    async def get_usage_trends(self, db_id, days=7):
        """Aggregates usage into hourly buckets for charts."""
        pipeline = [
            {"$match": {
                "metadata.user_id": self.user_id,
                "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)}
            }},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$timestamp", "unit": "hour"}},
                "total_ops": {"$count": {}},
                "avg_latency": {"$avg": "$latency_ms"}
            }},
            {"$sort": {"_id": 1}}
        ]
        return list(self.db["user_activity"].aggregate(pipeline))

    async def get_latest_storage(self, db_id):
        """Returns the most recent storage snapshot for a DB."""
        return self.db["storage_snapshots"].find_one(
            {"user_id": self.user_id, "db_id": db_id},
            sort=[("timestamp", -1)]
        )

    # api/services/analytics_service.py addition
    async def get_collection_schema_preview(self, db_name, coll_name):
        """
        Samples documents to tell the frontend what fields exist and their types.
        """
        db = settings.MONGODB_CLIENT[db_name]
        # Sample the last 100 documents to infer schema
        sample_docs = await db[coll_name].find().sort([("_id", -1)]).limit(100).to_list(100)
        
        schema = {}
        for doc in sample_docs:
            for key, value in doc.items():
                if key not in schema:
                    schema[key] = type(value).__name__
        
        return schema # Returns e.g., {"price": "float", "name": "str", "created_at": "datetime"}
