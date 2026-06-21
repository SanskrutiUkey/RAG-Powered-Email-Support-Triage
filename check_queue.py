import os
import redis
import ssl

from dotenv import load_dotenv
load_dotenv()
r = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True,
    ssl_cert_reqs=ssl.CERT_NONE
)

for queue in ["celery", "ai_processing"]:
    try:
        print(f"{queue}: {r.llen(queue)} messages")
    except Exception as e:
        print(queue, e)