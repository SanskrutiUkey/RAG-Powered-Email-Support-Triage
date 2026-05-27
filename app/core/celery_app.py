from celery import Celery

celery = Celery(
    "support_ai",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Use solo pool on Windows to avoid billiard permission issues
celery.conf.worker_pool = "solo"

celery.autodiscover_tasks(["app.core.tasks"])