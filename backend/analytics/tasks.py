import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task

from .services.analytics_services import AnalyticsService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, queue="analytics")
def log_http_request_task(self, data: dict):
    try:
        svc = AnalyticsService()
        svc.log_http_request(data)
    except Exception as e:
        logger.error("Failed to log HTTP request: %s", e)
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, queue="analytics")
def log_db_operation_task(self, data: dict):
    try:
        svc = AnalyticsService()
        svc.log_db_operation(data)
    except Exception as e:
        logger.error("Failed to log DB operation: %s", e)


@shared_task(bind=True, queue="analytics")
def log_performance_task(self, data: dict):
    try:
        svc = AnalyticsService()
        svc.log_performance_metrics(data)
    except Exception as e:
        logger.error("Failed to log performance metrics: %s", e)


@shared_task(bind=True, queue="analytics")
def log_client_info_task(self, data: dict):
    try:
        svc = AnalyticsService()
        svc.log_client_info(data)
    except Exception as e:
        logger.error("Failed to log client info: %s", e)


@shared_task(bind=True, queue="analytics")
def log_error_task(self, data: dict):
    try:
        svc = AnalyticsService()
        svc.log_error(data)
    except Exception as e:
        logger.error("Failed to log error: %s", e)


@shared_task(bind=True, queue="analytics")
def log_mongo_detail_task(self, data: dict):
    try:
        svc = AnalyticsService()
        svc.log_mongo_detail(data)
    except Exception as e:
        logger.error("Failed to log mongo detail: %s", e)


@shared_task(bind=True, queue="analytics")
def log_slow_query_task(self, data: dict):
    try:
        svc = AnalyticsService()
        svc.log_slow_query(data)
    except Exception as e:
        logger.error("Failed to log slow query: %s", e)


@shared_task(queue="analytics")
def aggregate_daily_usage():
    """
    Roll up per-user metrics for the previous UTC day.
    HTTP stats come from `http_requests`; top collections from `db_operations`
    (HTTP logs do not carry collection names).
    """
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    start = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    svc = AnalyticsService()
    time_filter = {"timestamp": {"$gte": start, "$lt": end}}

    pipeline_http = [
        {"$match": time_filter},
        {
            "$group": {
                "_id": "$user_id",
                "total_requests": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_ms"},
                "error_count": {"$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}},
            }
        },
    ]
    http_by_user = {}
    for doc in svc.db["http_requests"].aggregate(pipeline_http):
        uid = doc["_id"]
        http_by_user[uid] = {
            "total_requests": doc["total_requests"],
            "avg_duration": doc.get("avg_duration") or 0.0,
            "error_count": doc["error_count"],
        }

    pipeline_coll = [
        {"$match": {**time_filter, "collection": {"$exists": True, "$nin": ["", "system", "unknown"]}}},
        {
            "$group": {
                "_id": {"uid": "$user_id", "c": "$collection"},
                "n": {"$sum": 1},
            }
        },
        {"$sort": {"n": -1}},
        {
            "$group": {
                "_id": "$_id.uid",
                "items": {"$push": {"collection": "$_id.c", "operations": "$n"}},
            }
        },
        {"$project": {"user_id": "$_id", "top_collections": {"$slice": ["$items", 10]}}},
    ]
    coll_by_user = {}
    for doc in svc.db["db_operations"].aggregate(pipeline_coll):
        coll_by_user[doc["user_id"]] = doc.get("top_collections") or []

    all_users = set(http_by_user) | set(coll_by_user)
    for uid in all_users:
        h = http_by_user.get(
            uid,
            {"total_requests": 0, "avg_duration": 0.0, "error_count": 0},
        )
        total = int(h["total_requests"])
        err = int(h["error_count"])
        payload = {
            "user_id": uid,
            "date": date_str,
            "total_requests": total,
            "avg_duration_ms": float(h["avg_duration"]),
            "error_rate": (err / total) if total else 0.0,
            "top_collections": coll_by_user.get(uid, []),
            "top_endpoints": [],
        }
        svc.db["daily_aggregates"].update_one(
            {"user_id": uid, "date": date_str},
            {"$set": payload},
            upsert=True,
        )
    logger.info("Daily aggregation for %s completed (%s users)", date_str, len(all_users))


@shared_task(queue="maintenance")
def cleanup_old_analytics(days_to_keep=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    svc = AnalyticsService()
    collections = [
        "http_requests",
        "db_operations",
        "performance_metrics",
        "client_info",
        "errors",
        "mongo_details",
        "slow_queries",
    ]
    for coll in collections:
        result = svc.db[coll].delete_many({"timestamp": {"$lt": cutoff}})
        logger.info("Deleted %s documents from %s", result.deleted_count, coll)
