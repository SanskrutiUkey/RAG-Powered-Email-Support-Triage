import redis
import os
import ssl

redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True,
    ssl_cert_reqs=ssl.CERT_NONE
)