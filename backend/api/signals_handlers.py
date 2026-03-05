from django.dispatch import receiver
from .signals import post_import_signal, post_drop_signal
from .tasks import update_usage_stats_task, cleanup_dropped_db_telemetry

@receiver(post_import_signal)
def handle_post_import(sender, **kwargs):
    """
    When data is imported, trigger a background task to update 
    the user's usage statistics immediately.
    """
    user_id = kwargs.get("user_id")
    db_id = kwargs.get("db_id")
    count = kwargs.get("count")
    
    # Delay the task to Celery
    update_usage_stats_task.delay(user_id, db_id, count)

@receiver(post_drop_signal)
def handle_post_drop(sender, **kwargs):
    """
    When a database is dropped, clean up the 'platform_ops' logs 
    to save space.
    """
    db_id = kwargs.get("db_id")
    cleanup_dropped_db_telemetry.delay(db_id)
