import logging
from datetime import datetime, timedelta, timezone
import time
import json
from django.core.cache import cache # type: ignore

from celery import shared_task # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from asgiref.sync import async_to_sync # type: ignore

from api.services.metadata_service import MetadataService
from analytics.services.analytics_services import AnalyticsService
from api.utils.mongodb import get_sync_client
from core.utils.db import mongo_conn as auth_db


logger = logging.getLogger(__name__)
User = get_user_model()


def sync_run(coro):
    """Utility to run async service methods in sync Celery workers."""
    return async_to_sync(lambda: coro)()


@shared_task(queue='maintenance')
def collect_metrics():
    """
    Periodic task: Snapshots DB sizes and health for active users.
    Uses MongoDB users_collection instead of Django ORM.
    """
    # 1. Setup process-safe client
    client = get_sync_client()
    users_coll = auth_db.get_collection('users')


    active_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    
    # 2. Fetch active users from MongoDB
    # In 2026, we only fetch the 'user_id' to keep memory usage low
    cursor = users_coll.find(
        {
            "last_login": {"$gte": active_cutoff},
            "is_active": True
        },
        {"_id": 1}
    )
    
    # We use a list to close the cursor quickly
    active_users = cursor.to_list(length=1000)

    for user_doc in active_users:
        uid_str = str(user_doc["_id"])
        
        # 3. Use MetadataService to find real DBs linked to this tenant
        meta_svc = MetadataService(user_id=uid_str)
        db_result = sync_run(meta_svc.list_databases_paginated())
        
        # Unpack tuple (total, data) or raw list
        databases = db_result[1] if isinstance(db_result, tuple) else db_result

        svc = AnalyticsService(user_id=uid_str)
        
        for db_meta in databases:
            db_id = str(db_meta["_id"])
            internal_name = db_meta.get("dbName")
            
            if not internal_name:
                continue

            try:
                # 4. Use the specific tenant's database connection
                db_conn = client[internal_name]
                stats = sync_run(db_conn.command("dbStats"))

                metrics = {
                    "doc_count": stats.get("objects", 0),
                    "size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                    "storage_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                    "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2),
                }

                # 5. Save to Time Series collection
                svc.collect_time_series_metrics(db_id, metrics)
                
            except Exception as e:
                logger.warning(f"Metrics failed for DB {db_id} (User: {uid_str}): {e}")


@shared_task(queue='maintenance')
def aggregate_daily_usage():
    """Compacts raw telemetry into daily summaries for frontend speed."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    svc = AnalyticsService(user_id="SYSTEM_AGGREGATOR")

    svc.run_daily_compaction(target_date=yesterday) 
    logger.info(f"Daily compaction completed for {yesterday.date()}")


@shared_task(queue='maintenance')
def cleanup_old_logs(days_to_keep: int = 30):
    """Purges stale raw logs while preserving daily summaries."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    client = get_sync_client()
    db = client["platform_ops"]

    result = db["user_activity"].delete_many({"timestamp": {"$lt": cutoff}})
    logger.info(f"Cleanup: Removed {result.deleted_count} stale logs.")


@shared_task(bind=True, max_retries=3, queue='analytics')
def log_request_metrics_task(self, data: dict):
    """Logs API telemetry dispatched from middleware."""
    try:
        user_id = data.get("user_id")
        if not user_id:
            logger.warning("No user_id in telemetry data")
            return

        svc = AnalyticsService(user_id=user_id)
        
        # Extract key metrics
        duration = data.get("duration_ms", 0)
        method = data.get("method", "UNKNOWN")
        path = data.get("path", "/")
        status_code = data.get("status_code", 200)
        db_id = data.get("db_id")
        collection = data.get("collection", "unknown")
        endpoint_category = data.get("endpoint_category", "unknown")
        timestamp = data.get("timestamp", int(time.time() * 1000))
        
        # Convert timestamp to datetime for time-based analysis
        event_time = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)

        # 1. Log General Navigation with enhanced details
        navigation_details = {
            'path': path,
            'method': method,
            'status_code': status_code,
            'endpoint_category': endpoint_category,
            'client_ip': data.get("client_ip", ""),
            'user_agent': data.get("user_agent", "")[:100],  # Truncate
            'timestamp': event_time.isoformat(),
        }
        
        if db_id:
            navigation_details['db_id'] = db_id
        if collection != 'unknown':
            navigation_details['collection'] = collection
            
        svc.log_usage(
            action=f"{method}_{endpoint_category}",
            details=navigation_details
        )

        # 2. Log Database-specific metrics for MongoDB operations
        if any(keyword in path.lower() for keyword in ['crud', 'import', 'data', 'database', 'collection']):
            # Determine IO type based on method and endpoint
            if method == 'GET':
                io_type = 'read'
                operation_desc = 'query'
            elif method in ['POST', 'PUT']:
                io_type = 'write'
                operation_desc = 'insert_update'
            elif method == 'DELETE':
                io_type = 'write'
                operation_desc = 'delete'
            else:
                io_type = 'read' if method == 'GET' else 'write'
                operation_desc = 'other'
            
            # MongoDB-specific metrics
            mongo_metrics = {
                'operation': data.get("mongo_operation", "unknown"),
                'document_count': data.get("document_count", 0),
                'query_complexity': data.get("query_complexity", "simple"),
                'collection': collection,
                'db_id': db_id,
                'success': data.get("success", True),
                'request_size': data.get("request_size_bytes", 0),
                'response_size': data.get("response_size_bytes", 0),
                'throughput': data.get("throughput_bytes_per_sec", 0),
            }
            
            # Add MongoDB operation counts if available
            for count_field in ['inserted_count', 'modified_count', 'deleted_count', 'returned_documents']:
                if count_field in data:
                    mongo_metrics[count_field] = data[count_field]
            
            svc.log_io(
                io_type=io_type,
                collection=collection,
                duration_ms=duration,
                success=status_code < 400,
                details={
                    'operation': operation_desc,
                    'mongo_metrics': mongo_metrics,
                    'endpoint': path,
                    'method': method,
                }
            )

        # 3. Decision Gate: Log as slow query if threshold exceeded
        # Use dynamic thresholds based on operation type
        slow_threshold = get_slow_threshold(
            operation=data.get("mongo_operation", "unknown"),
            endpoint_category=endpoint_category
        )
        
        if duration > slow_threshold:
            slow_query_details = {
                'query': {
                    'method': method,
                    'path': path,
                    'endpoint_category': endpoint_category,
                    'params': data.get("query_params", {}),
                    'request_body_size': data.get("request_size_bytes", 0),
                    'response_body_size': data.get("response_size_bytes", 0),
                },
                'duration_ms': duration,
                'threshold_ms': slow_threshold,
                'collection': collection,
                'db_id': db_id,
                'mongo_operation': data.get("mongo_operation", "unknown"),
                'document_count': data.get("document_count", 0),
                'performance_warning': data.get("performance_warning", ""),
            }
            
            # Add request/response snippets for debugging (truncated)
            if not data.get("is_production", False):  # Only in non-prod
                request_body = data.get("request_body", {})
                response_body = data.get("response_body", {})
                
                if request_body:
                    slow_query_details['request_snippet'] = truncate_data(request_body, max_length=500)
                if response_body:
                    slow_query_details['response_snippet'] = truncate_data(response_body, max_length=500)
            
            svc.log_slow_query(
                query=slow_query_details['query'], 
                duration_ms=duration,
                details=slow_query_details
            )
            
            # Increment slow query counter for alerting
            track_slow_query_pattern(collection, endpoint_category, duration)

        # 4. Track performance patterns for capacity planning
        track_performance_patterns(data)

        # 5. Update real-time dashboard cache
        update_realtime_metrics(data)

    except Exception as exc:
        logger.error(f"Telemetry task failed: {exc}", exc_info=True)
        
        # Don't retry specific types of errors
        if "event loop" in str(exc).lower():
            logger.critical(f"Loop conflict in worker: {exc}")
            return
        elif "validation" in str(exc).lower():
            logger.warning(f"Data validation error: {exc}")
            return
        
        # Exponential backoff retry
        retry_count = self.request.retries
        countdown = min(5 * (2 ** retry_count), 60)  # Max 60 seconds
        
        logger.warning(f"Retrying task in {countdown}s (attempt {retry_count + 1})")
        raise self.retry(exc=exc, countdown=countdown)


def get_slow_threshold(operation: str, endpoint_category: str) -> int:
    """Get dynamic slow query threshold based on operation type."""
    # Base thresholds in milliseconds
    thresholds = {
        # Database operations
        'database_creation': 3000,
        'database_deletion': 2000,
        'database_listing': 1000,
        
        # Collection operations
        'collection_creation': 2000,
        'collection_deletion': 1500,
        'collection_listing': 1000,
        
        # Document operations
        'document_creation': 1000,
        'document_update': 1000,
        'document_deletion': 800,
        'document_query': 500,
        'bulk_insert': 5000,  # Bulk operations take longer
        'single_insert': 800,
        
        # Data operations
        'data_import': 10000,  # Large imports can take time
        'metadata_retrieval': 500,
        
        # Defaults
        'read': 500,
        'write': 1000,
        'unknown': 1000,
    }
    
    # Try operation-specific first, then endpoint category
    if operation in thresholds:
        return thresholds[operation]
    elif endpoint_category in thresholds:
        return thresholds[endpoint_category]
    else:
        return 1000  # Default threshold


def truncate_data(data, max_length=500):
    """Truncate data for logging to prevent excessive storage."""
    try:
        json_str = json.dumps(data)
        if len(json_str) > max_length:
            return json_str[:max_length] + "..."
        return json_str
    except:
        return str(data)[:max_length]


def track_slow_query_pattern(collection: str, endpoint: str, duration: float):
    """Track patterns of slow queries for alerting."""
    cache_key = f"slow_queries:{collection}:{endpoint}"
    
    # Track last 10 slow queries
    slow_queries = cache.get(cache_key, [])
    slow_queries.append({
        'timestamp': time.time(),
        'duration': duration,
    })
    
    # Keep only last 10 entries
    if len(slow_queries) > 10:
        slow_queries = slow_queries[-10:]
    
    cache.set(cache_key, slow_queries, timeout=3600)  # Keep for 1 hour
    
    # Check if we need to alert (e.g., 3 slow queries in 5 minutes)
    recent_slow = [q for q in slow_queries if time.time() - q['timestamp'] < 300]
    if len(recent_slow) >= 3:
        alert_key = f"alert_sent:{collection}:{endpoint}"
        if not cache.get(alert_key):
            logger.warning(
                f"Slow query alert: {collection}/{endpoint} has {len(recent_slow)} "
                f"slow queries in last 5 minutes"
            )
            cache.set(alert_key, True, timeout=300)  # Don't alert again for 5 minutes


def track_performance_patterns(data: dict):
    """Track performance patterns for capacity planning."""
    collection = data.get("collection", "unknown")
    db_id = data.get("db_id", "unknown")
    duration = data.get("duration_ms", 0)
    document_count = data.get("document_count", 0)
    
    # Track average response time per collection
    avg_key = f"perf_avg:{collection}"
    count_key = f"perf_count:{collection}"
    
    current_avg = cache.get(avg_key, 0)
    current_count = cache.get(count_key, 0)
    
    # Update moving average
    new_avg = ((current_avg * current_count) + duration) / (current_count + 1)
    cache.set(avg_key, new_avg, timeout=86400)  # 24 hours
    cache.set(count_key, current_count + 1, timeout=86400)
    
    # Track document count patterns for bulk operations
    if document_count > 0:
        doc_key = f"doc_pattern:{collection}"
        doc_patterns = cache.get(doc_key, {'counts': [], 'timestamps': []})
        
        doc_patterns['counts'].append(document_count)
        doc_patterns['timestamps'].append(time.time())
        
        # Keep last 100 entries
        if len(doc_patterns['counts']) > 100:
            doc_patterns['counts'] = doc_patterns['counts'][-100:]
            doc_patterns['timestamps'] = doc_patterns['timestamps'][-100:]
        
        cache.set(doc_key, doc_patterns, timeout=86400)


def update_realtime_metrics(data: dict):
    """Update real-time dashboard metrics."""
    try:
        # Update request rate counters
        minute_key = f"realtime:requests:{int(time.time() / 60)}"
        # Ensure the counter exists and has a TTL; set when creating, incr otherwise.
        if cache.get(minute_key) is None:
            cache.set(minute_key, 1, timeout=120)
        else:
            try:
                cache.incr(minute_key)
            except Exception:
                cache.set(minute_key, cache.get(minute_key, 0) + 1, timeout=120)
        
        # Update endpoint-specific counters
        endpoint = data.get("path", "unknown")
        endpoint_key = f"realtime:endpoint:{endpoint}"
        if cache.get(endpoint_key) is None:
            cache.set(endpoint_key, 1, timeout=300)
        else:
            try:
                cache.incr(endpoint_key)
            except Exception:
                cache.set(endpoint_key, cache.get(endpoint_key, 0) + 1, timeout=300)
        
        # Update error rate if applicable
        if data.get("status_code", 200) >= 400:
            error_key = f"realtime:errors:{endpoint}"
            # incr does not accept a timeout; ensure the key exists with TTL, then increment
            if cache.get(error_key) is None:
                cache.set(error_key, 1, timeout=300)
            else:
                try:
                    cache.incr(error_key)
                except Exception:
                    cache.set(error_key, cache.get(error_key, 0) + 1, timeout=300)
            
    except Exception as e:
        logger.debug(f"Failed to update realtime metrics: {e}")


@shared_task(bind=True, queue='analytics')
def analyze_mongo_performance_patterns(self, days_back=7):
    """Analyze MongoDB performance patterns over time."""
    try:
        # svc = AnalyticsService(user_id="SYSTEM_ANALYZER")
        
        # This would query your analytics database
        # to find patterns like:
        # - Most frequent collections
        # - Peak usage times
        # - Average document sizes
        # - Index usage patterns
        
        logger.info(f"Running MongoDB performance analysis for last {days_back} days")
        
        # Example analysis logic:
        current_time = time.time()
        start_time = current_time - (days_back * 24 * 3600)
        
        # You would implement actual analysis here, for example:
        # 1. Query analytics database for the time period
        # 2. Calculate statistics
        # 3. Generate reports
        # 4. Send alerts if needed
        
        # For now, just log
        logger.info(f"Analyzing data from {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(current_time)}")
        
    except Exception as e:
        logger.error(f"MongoDB analysis task failed: {e}")


@shared_task(bind=True, queue='analytics')
def cleanup_old_telemetry(self, days_to_keep=30):
    """Clean up old telemetry data."""
    try:
        # Implementation depends on your storage
        # Could delete old records from analytics database
        
        logger.info(f"Cleaning up telemetry older than {days_to_keep} days")
        
        # Example implementation (adjust based on your storage):
        # current_time = time.time()
        # cutoff_time = current_time - (days_to_keep * 24 * 3600)
        
        # If using MongoDB for analytics:
        # from .models import TelemetryRecord
        # TelemetryRecord.objects.filter(timestamp__lt=cutoff_time).delete()
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")


@shared_task(queue='analytics')
def aggregate_realtime_metrics():
    """Aggregate real-time metrics into historical data."""
    try:
        logger.info("Aggregating real-time metrics")
        
        # This task would:
        # 1. Read from cache
        # 2. Aggregate minute-by-minute data into hourly summaries
        # 3. Store in persistent storage
        # 4. Clear old cache entries
        
        current_time = time.time()
        current_minute = int(current_time / 60)
        
        # Example: Aggregate requests per minute
        for minute_offset in range(60, 0, -1):  # Last 60 minutes
            minute_key = f"realtime:requests:{current_minute - minute_offset}"
            request_count = cache.get(minute_key)
            
            if request_count:
                # Store aggregated data
                logger.debug(f"Minute {current_minute - minute_offset}: {request_count} requests")
                # Clear the cache entry
                cache.delete(minute_key)
                
    except Exception as e:
        logger.error(f"Failed to aggregate realtime metrics: {e}")


@shared_task(bind=True, queue='alerts')
def check_performance_alerts(self):
    """Check and send performance alerts."""
    try:
        logger.info("Checking performance alerts")
        
        # Check for various alert conditions:
        
        # 1. High error rate alerts
        error_threshold = 0.1  # 10% error rate
        endpoints_to_check = ['/api/crud/', '/api/import_data/', '/api/create_database/']
        
        for endpoint in endpoints_to_check:
            error_key = f"realtime:errors:{endpoint}"
            request_key = f"realtime:endpoint:{endpoint}"
            
            error_count = cache.get(error_key, 0)
            request_count = cache.get(request_key, 0)
            
            if request_count > 10 and error_count / request_count > error_threshold:
                logger.warning(f"High error rate for {endpoint}: {error_count}/{request_count} errors")
                # Send alert (email, Slack, etc.)
                # send_alert(f"High error rate on {endpoint}: {(error_count/request_count)*100:.1f}%")
        
        # 2. Slow query pattern alerts
        # Check cache for slow query patterns tracked by track_slow_query_pattern
        
        # 3. System health checks
        # Add more checks as needed
        
    except Exception as e:
        logger.error(f"Failed to check performance alerts: {e}")


@shared_task(queue='analytics')
def generate_daily_report():
    """Generate daily analytics report."""
    try:
        logger.info("Generating daily analytics report")
        
        # Generate report data
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_data = {
            'date': report_date,
            'total_requests': 0,
            'avg_response_time': 0,
            'top_endpoints': [],
            'error_rate': 0,
            'slow_queries': [],
        }
        
        # This would query your analytics database
        # and generate a comprehensive report
        
        # For now, just log
        logger.info(f"Daily report generated for {report_date}")
        
        # Could send report via email or store for dashboard
        # send_email_report(report_data)
        
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")



















# @shared_task(bind=True, max_retries=3, queue='analytics')
# def log_request_metrics_task(self, data: dict):
#     """Logs API telemetry dispatched from middleware."""
#     try:
#         user_id = data.get("user_id")
#         if not user_id:
#             return

#         svc = AnalyticsService(user_id=user_id)
        
#         duration = data.get("duration_ms", 0)
#         method = data.get("method", "UNKNOWN")
#         path = data.get("path", "/")
#         status_code = data.get("status_code", 200)

#         # 1. Log General Navigation
#         sync_run(svc.log_usage(action=method, details={'path': path, 'status': status_code}))

#         # 2. Log IO Stats specifically for CRUD and Import paths
#         if any(keyword in path.lower() for keyword in ['crud', 'import', 'data']):
#             sync_run(svc.log_io(
#                 io_type='read' if method == 'GET' else 'write',
#                 collection=data.get("collection", "unknown"),
#                 duration_ms=duration,
#                 success=status_code < 400
#             ))

#         # 3. Decision Gate: Log as slow query if threshold exceeded
#         if duration > 200:
#             sync_run(svc.log_slow_query(
#                 query={'method': method, 'path': path, 'params': data.get("query_params")}, 
#                 duration_ms=duration
#             ))

#     except Exception as exc:
#         if "event loop" in str(exc).lower():
#             logger.critical(f"Loop conflict in worker: {exc}")
#             return
            
#         logger.error(f"Telemetry task failed: {exc}")
#         raise self.retry(exc=exc, countdown=5)
