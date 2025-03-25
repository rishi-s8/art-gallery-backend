import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcp_nexus.settings')

app = Celery('mcp_nexus')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Define periodic tasks
app.conf.beat_schedule = {
    'check-server-health-hourly': {
        'task': 'verification.tasks.run_scheduled_health_checks',
        'schedule': crontab(minute=0),  # Run every hour
    },
    'generate-daily-network-analytics': {
        'task': 'analytics.tasks.generate_daily_network_analytics',
        'schedule': crontab(hour=1, minute=0),  # Run at 1:00 AM
    },
    'clean-old-request-logs-weekly': {
        'task': 'analytics.tasks.clean_old_request_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Run at 2:00 AM every Monday
    },
    'aggregate-client-analytics-daily': {
        'task': 'analytics.tasks.aggregate_client_analytics',
        'schedule': crontab(hour=3, minute=0),  # Run at 3:00 AM
    },
    'clean-old-webhook-deliveries-weekly': {
        'task': 'webhooks.tasks.clean_old_webhook_deliveries',
        'schedule': crontab(hour=4, minute=0, day_of_week=2),  # Run at 4:00 AM every Tuesday
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')