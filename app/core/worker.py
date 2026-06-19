# import json
# import time
# import logging
# from app.core.redis import redis_client

# print("Worker started...")
# logger = logging.getLogger(__name__)

# while True:
#     queue_size = redis_client.llen(
#         "ai_processing"
#     )
#     job = redis_client.brpop("support_email_queue")

#     if job:
#         _, payload = job

#         data = json.loads(payload)

#         logger.info(
#             f"QUEUE_SIZE={queue_size}"
#         )

#         # AI processing here

#         time.sleep(2)