import logging
import asyncio
from datetime import datetime, timedelta, timezone

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync

from api.services.metadata_service import MetadataService
from analytics.services.analytics_services import AnalyticsService
from api.utils.mongodb import get_async_client

logger = logging.getLogger(__name__)
User = get_user_model()

def sync_run(coro):
    """Utility to run async service methods in sync Celery workers."""
    return async_to_sync(lambda: coro)()

@shared_task(queue='maintenance')
def collect_metrics():
    """
    Periodic task: Snapshots DB sizes and health for active users.
    """
    active_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    # Optimization: Only select IDs to reduce memory footprint
    user_ids = User.objects.filter(
        last_login__gte=active_cutoff, 
        is_active=True
    ).values_list('id', flat=True)

    client = get_async_client()

    for user_id in user_ids:
        uid_str = str(user_id)
        meta_svc = MetadataService(user_id=uid_str)
        
        # FIX: list_databases_paginated typically returns (total, [databases])
        # We handle both cases (tuple or list) for resilience
        db_result = sync_run(meta_svc.list_databases_paginated())
        databases = db_result[1] if isinstance(db_result, tuple) else db_result

        svc = AnalyticsService(user_id=uid_str)
        
        for db_meta in databases:
            db_id = str(db_meta["_id"])
            internal_name = db_meta.get("dbName")
            
            if not internal_name:
                continue

            try:
                db_conn = client[internal_name]
                # Use 'storageStats' for 2026 MongoDB compatibility
                stats = sync_run(db_conn.command("dbStats"))

                metrics = {
                    "doc_count": stats.get("objects", 0),
                    "size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                    "storage_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                    "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2),
                }

                sync_run(svc.collect_time_series_metrics(db_id, metrics))
                
            except Exception as e:
                logger.warning(f"Metrics failed for DB {db_id} (User: {uid_str}): {e}")

@shared_task(queue='maintenance')
def aggregate_daily_usage():
    """Compacts raw telemetry into daily summaries for frontend speed."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    # Using a system-level context for global aggregation
    svc = AnalyticsService(user_id="SYSTEM_AGGREGATOR")
    
    sync_run(svc.run_daily_compaction(target_date=yesterday))
    logger.info(f"Daily compaction completed for {yesterday.date()}")

@shared_task(queue='maintenance')
def cleanup_old_logs(days_to_keep: int = 30):
    """Purges stale raw logs while preserving daily summaries."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    # Get client process-safely
    client = get_async_client()
    db = client["platform_ops"]
    
    result = sync_run(db["user_activity"].delete_many({"timestamp": {"$lt": cutoff}}))
    logger.info(f"Cleanup: Removed {result.deleted_count} stale logs.")

@shared_task(bind=True, max_retries=3, queue='analytics')
def log_request_metrics_task(self, data: dict):
    """Logs API telemetry dispatched from middleware."""
    try:
        user_id = data.get("user_id")
        if not user_id:
            return

        svc = AnalyticsService(user_id=user_id)
        
        # Extraction with defaults to prevent KeyErrors
        duration = data.get("duration_ms", 0)
        method = data.get("method", "UNKNOWN")
        path = data.get("path", "/")
        status_code = data.get("status_code", 200)

        # 1. Log General Navigation
        sync_run(svc.log_usage(action=method, details={'path': path, 'status': status_code}))

        # 2. Log IO Stats specifically for CRUD and Import paths
        if any(keyword in path for keyword in ['crud', 'import', 'data']):
            sync_run(svc.log_io(
                io_type='read' if method == 'GET' else 'write',
                collection=data.get("collection", "unknown"),
                duration_ms=duration,
                success=status_code < 400
            ))

        # 3. Decision Gate: Log as slow query if threshold exceeded
        if duration > 200: # Slightly higher threshold for 2026 workloads
            sync_run(svc.log_slow_query(
                query={'method': method, 'path': path, 'params': data.get("query_params")}, 
                duration_ms=duration
            ))

    except Exception as exc:
        # Avoid retrying loop-related config errors
        if "event loop" in str(exc).lower():
            logger.critical(f"Loop conflict in worker: {exc}")
            return
            
        logger.error(f"Telemetry task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)
