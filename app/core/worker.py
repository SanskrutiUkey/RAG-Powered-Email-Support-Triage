import json
import time

from app.core.redis import redis_client

print("Worker started...")

while True:
    job = redis_client.brpop("support_email_queue")

    if job:
        _, payload = job

        data = json.loads(payload)

        print("PROCESSING:", data)

        # AI processing here

        time.sleep(2)