import os
import ssl
from celery import Celery
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv("REDIS_URL")

celery = Celery(
    "ai_processing",
    broker=redis_url,
    backend=redis_url,
)

celery.conf.broker_use_ssl = {
    "ssl_cert_reqs": ssl.CERT_NONE
}

celery.conf.redis_backend_use_ssl = {
    "ssl_cert_reqs": ssl.CERT_NONE
}
# Use solo pool on Windows to avoid billiard permission issues
celery.conf.worker_pool = "solo"

celery.autodiscover_tasks(["app.core.tasks"])