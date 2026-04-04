import os
from celery import Celery
from celery.schedules import crontab


# 1. Set environment defaults
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings.production')

app = Celery('datacube') # type: ignore # Renamed to align with your app name

# 2. Optimized Configuration
app.config_from_object('django.conf:settings', namespace='CELERY')

# 3. 2026 Performance Tuning
app.conf.update(
    # Timezone alignment
    timezone='Africa/Lagos',
    enable_utc=True,  # Recommended: Store UTC internally, convert in UI
    
    # Task Reliability
    task_acks_late=True,             # Task acknowledged only after execution
    task_reject_on_worker_lost=True, # Requeue task if worker crashes
    worker_prefetch_multiplier=1,    # One task per worker at a time (prevents bottlenecks)
    
    # Resource Limits
    worker_max_tasks_per_child=1000, # Restart worker to prevent memory leaks
    task_time_limit=300,             # Hard limit: 5 mins
    task_soft_time_limit=240,        # Soft limit: 4 mins (raises exception)
    
    # Routing (Separates "Fast" logs from "Heavy" cleanup)
    task_routes={
        'analytics.tasks.log_request_metrics_task': {'queue': 'analytics'},
        'analytics.tasks.cleanup_old_logs': {'queue': 'maintenance'},
    }
)

# 4. Auto-discover tasks in all apps (analytics, api, etc.)
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Datacube Celery Heartbeat: {self.request!r}')

# 5. Strategic Beat Schedule for Datacube
app.conf.beat_schedule = {
    # STORAGE SNAPSHOTS: High frequency for accurate "Quota" enforcement
    'snapshot-db-sizes-every-15-min': {
        'task': 'analytics.tasks.collect_metrics', # Should map to dbStats/collStats
        'schedule': crontab(minute='*/15'),
    },

    # DATA AGGREGATION: Compacting raw telemetry into daily buckets for Recharts
    'daily-usage-compaction': {
        'task': 'analytics.tasks.aggregate_daily_usage',
        'schedule': crontab(hour=2, minute=30),
    },

    # SYSTEM HYGIENE: Weekly cleanup to prevent platform_ops from exploding
    'weekly-log-pruning': {
        'task': 'analytics.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
    },

    # BUSINESS REPORTING: Monthly data snapshots for tenant billing/reports
    'monthly-tenant-reports': {
        'task': 'analytics.tasks.create_monthly_snapshot',
        'schedule': crontab(day_of_month=1, hour=1, minute=0),
    },
}
