import os 
from celery import Celery

celery = Celery(
    "ai_processing",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

# Use solo pool on Windows to avoid billiard permission issues
celery.conf.worker_pool = "solo"

celery.autodiscover_tasks(["app.core.tasks"])