import logging
import os
from typing import Dict, Any

from django.conf import settings

from pymongo import ASCENDING, DESCENDING

from ..schemas import (
    HttpRequestSchema, DatabaseContextSchema, PerformanceMetricsSchema,
    ClientInfoSchema, ErrorSchema, MongoDetailSchema, SlowQuerySchema
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self):
        # Use a separate connection for analytics (optional, but recommended)
        self.client = settings.SYNC_MONGODB_CLIENT
        self.db = self.client["datacube_analytics"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for optimal querying (idempotent)."""
        # http_requests
        self.db["http_requests"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        self.db["http_requests"].create_index([("timestamp", DESCENDING)])
        # db_operations
        self.db["db_operations"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        self.db["db_operations"].create_index([("db_id", ASCENDING)])
        # performance_metrics
        self.db["performance_metrics"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        # client_info
        self.db["client_info"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        # errors
        self.db["errors"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        self.db["errors"].create_index([("status_code", ASCENDING)])
        # mongo_details
        self.db["mongo_details"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        # slow_queries
        self.db["slow_queries"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        self.db["daily_aggregates"].create_index([("user_id", ASCENDING), ("date", DESCENDING)])
        self._ensure_ttl_indexes()

    def _ensure_ttl_indexes(self) -> None:
        """
        Optional TTL on high-volume telemetry (MongoDB deletes documents automatically).
        Set ANALYTICS_TTL_DAYS_TELEMETRY=0 to disable. Default 90 days.
        """
        raw = os.getenv("ANALYTICS_TTL_DAYS_TELEMETRY", "90").strip()
        try:
            days = int(raw)
        except ValueError:
            days = 90
        if days <= 0:
            return
        expire_after = days * 86400
        for coll in ("http_requests", "client_info", "performance_metrics"):
            name = f"ttl_timestamp_{coll}"
            try:
                self.db[coll].create_index(
                    [("timestamp", ASCENDING)],
                    expireAfterSeconds=expire_after,
                    name=name,
                )
            except Exception as exc:
                logger.warning("TTL index on %s not created or already differs: %s", coll, exc)

    def log_http_request(self, data: Dict[str, Any]):
        """Insert one HTTP request log."""
        schema_instance = HttpRequestSchema(**data)
        self.db["http_requests"].insert_one(schema_instance.model_dump())

    def log_db_operation(self, data: Dict[str, Any]):
        schema_instance = DatabaseContextSchema(**data)
        self.db["db_operations"].insert_one(schema_instance.model_dump())

    def log_performance_metrics(self, data: Dict[str, Any]):
        schema_instance = PerformanceMetricsSchema(**data)
        self.db["performance_metrics"].insert_one(schema_instance.model_dump())

    def log_client_info(self, data: Dict[str, Any]):
        schema_instance = ClientInfoSchema(**data)
        self.db["client_info"].insert_one(schema_instance.model_dump())

    def log_error(self, data: Dict[str, Any]):
        schema_instance = ErrorSchema(**data)
        self.db["errors"].insert_one(schema_instance.model_dump())

    def log_mongo_detail(self, data: Dict[str, Any]):
        schema_instance = MongoDetailSchema(**data)
        self.db["mongo_details"].insert_one(schema_instance.model_dump())

    def log_slow_query(self, data: Dict[str, Any]):
        schema_instance = SlowQuerySchema(**data)
        self.db["slow_queries"].insert_one(schema_instance.model_dump())

    # Bulk insertion for high throughput (optional)
    def bulk_log_http_requests(self, docs: list):
        if docs:
            self.db["http_requests"].insert_many(docs)
