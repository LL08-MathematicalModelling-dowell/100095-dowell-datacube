import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model
from .tasks import log_request_metrics_task, cleanup_old_logs

User = get_user_model()
logger = logging.getLogger('datacube.signals')

# --- Custom Datacube Signals ---
# Use dispatch_uid to prevent duplicate signal registration in some environments
document_imported = Signal()  # args: [user_id, db_id, coll_name, count]
database_dropped = Signal()   # args: [user_id, db_id]

@receiver(post_save, sender=User, dispatch_uid="bootstrap_tenant_signal")
def user_created_handler(sender, instance, created, **kwargs):
    """
    Bootstrap a new tenant in Datacube.
    """
    if created:
        logger.info(f"Bootstrapping Datacube tenant: {instance.email} (ID: {instance.pk})")
        
        # Log 'Sign Up' event to telemetry background queue
        log_request_metrics_task.delay({
            "user_id": str(instance.pk),
            "method": "SIGNAL",
            "path": "/account/signup",
            "status_code": 201,
            "duration_ms": 0,
            "collection": "system",
            "metadata": {"source": "post_save_signal"}
        })

@receiver(post_delete, sender=User, dispatch_uid="cleanup_tenant_signal")
def user_deleted_handler(sender, instance, **kwargs):
    """
    Security Cleanup: Offload heavy data purging to the maintenance queue.
    """
    user_id = str(instance.pk)
    logger.warning(f"Tenant {user_id} deleted. Initiating global telemetry purge.")
    
    # Priority: Maintenance queue to avoid blocking high-frequency analytics workers
    cleanup_old_logs.apply_async(
        kwargs={'user_id': user_id},
        queue='maintenance' 
    )

# --- Custom Handlers for MongoDB Events ---

@receiver(document_imported, dispatch_uid="bulk_import_metrics_handler")
def handle_bulk_import_metrics(sender, **kwargs):
    """
    Updates 'Write' telemetry immediately after a NoSQL bulk operation.
    """
    user_id = kwargs.get("user_id")
    db_id = kwargs.get("db_id")
    
    # Validation check: Ensure required data is present
    if not user_id or not db_id:
        logger.error("document_imported signal received without user_id or db_id")
        return

    log_request_metrics_task.delay({
        "user_id": str(user_id),
        "method": "IMPORT",
        "path": f"/api/import/{db_id}",
        "status_code": 201,
        "duration_ms": 0,
        "collection": kwargs.get("coll_name", "unknown")
    })
