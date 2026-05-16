import logging
import os

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.production")

app = Celery("datacube")  # type: ignore

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_routes={
        "analytics.tasks.log_http_request_task": {"queue": "analytics"},
        "analytics.tasks.log_db_operation_task": {"queue": "analytics"},
        "analytics.tasks.log_performance_task": {"queue": "analytics"},
        "analytics.tasks.log_client_info_task": {"queue": "analytics"},
        "analytics.tasks.log_error_task": {"queue": "analytics"},
        "analytics.tasks.log_mongo_detail_task": {"queue": "analytics"},
        "analytics.tasks.log_slow_query_task": {"queue": "analytics"},
        "analytics.tasks.aggregate_daily_usage": {"queue": "analytics"},
        "analytics.tasks.cleanup_old_analytics": {"queue": "maintenance"},
    },
)

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.debug("Datacube Celery heartbeat: %r", self.request)


app.conf.beat_schedule = {
    "daily-usage-compaction": {
        "task": "analytics.tasks.aggregate_daily_usage",
        "schedule": crontab(hour=2, minute=30),
    },
    "weekly-analytics-prune": {
        "task": "analytics.tasks.cleanup_old_analytics",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
}
