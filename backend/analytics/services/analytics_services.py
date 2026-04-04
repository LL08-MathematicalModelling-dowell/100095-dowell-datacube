import logging
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
        self.db["slow_queries"].create_index([("duration_ms", DESCENDING)])

    def log_http_request(self, data: Dict[str, Any]):
        """Insert one HTTP request log."""
        schema = HttpRequestSchema(**data)
        self.db["http_requests"].insert_one(schema.dict(by_alias=True))

    def log_db_operation(self, data: Dict[str, Any]):
        schema = DatabaseContextSchema(**data)
        self.db["db_operations"].insert_one(schema.dict(by_alias=True))

    def log_performance_metrics(self, data: Dict[str, Any]):
        schema = PerformanceMetricsSchema(**data)
        self.db["performance_metrics"].insert_one(schema.dict(by_alias=True))

    def log_client_info(self, data: Dict[str, Any]):
        schema = ClientInfoSchema(**data)
        self.db["client_info"].insert_one(schema.dict(by_alias=True))

    def log_error(self, data: Dict[str, Any]):
        schema = ErrorSchema(**data)
        self.db["errors"].insert_one(schema.dict(by_alias=True))

    def log_mongo_detail(self, data: Dict[str, Any]):
        schema = MongoDetailSchema(**data)
        self.db["mongo_details"].insert_one(schema.dict(by_alias=True))

    def log_slow_query(self, data: Dict[str, Any]):
        schema = SlowQuerySchema(**data)
        self.db["slow_queries"].insert_one(schema.dict(by_alias=True))

    # Bulk insertion for high throughput (optional)
    def bulk_log_http_requests(self, docs: list):
        if docs:
            self.db["http_requests"].insert_many(docs)
