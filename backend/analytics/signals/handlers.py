import logging
from django.dispatch import receiver
from .definitions import (
    post_import_signal, post_drop_signal, 
    quota_reached_signal, document_created_signal
)
from analytics.tasks import log_request_metrics_task, cleanup_old_logs


logger = logging.getLogger('datacube.signals')

@receiver(post_import_signal, dispatch_uid="dc_bulk_import_handler")
def handle_bulk_import(sender, **kwargs):
    """Bridge for bulk ingestion telemetry."""
    log_request_metrics_task.delay({
        "user_id": kwargs.get("user_id"),
        "method": "IMPORT",
        "path": f"/api/import/{kwargs.get('db_id')}",
        "status_code": 201,
        "collection": kwargs.get("coll_name"),
        "metadata": {"bulk_count": kwargs.get("count")}
    })

@receiver(document_created_signal, dispatch_uid="dc_crud_create_handler")
def handle_crud_create(sender, **kwargs):
    """Bridge for standard CRUD telemetry."""
    log_request_metrics_task.delay({
        "user_id": kwargs.get("user_id"),
        "method": "POST",
        "path": "/api/crud",
        "status_code": 201,
        "collection": kwargs.get("coll_name"),
        "metadata": {"count": kwargs.get("count", 1)}
    })

@receiver(quota_reached_signal, dispatch_uid="dc_quota_warning_handler")
def handle_quota_limit(sender, **kwargs):
    """Critical: Logs a block event for the dashboard when quota is hit."""
    logger.error(f"Quota reached for user {kwargs.get('user_id')}")
    log_request_metrics_task.delay({
        "user_id": kwargs.get("user_id"),
        "method": "BLOCK",
        "path": "QUOTA_GATE",
        "status_code": 403,
        "metadata": {
            "usage": kwargs.get("usage_bytes"),
            "limit": kwargs.get("limit_bytes")
        }
    })

@receiver(post_drop_signal, dispatch_uid="dc_cleanup_handler")
def handle_db_drop(sender, **kwargs):
    """Triggers global telemetry purge for the dropped database."""
    # Route specifically to 'maintenance' queue
    cleanup_old_logs.apply_async(
        kwargs={'db_id': kwargs.get('db_id')},
        queue='maintenance'
    )
