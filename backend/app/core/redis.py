import redis
from rq import Queue

from app.core.config import settings


# ---------------------------------------------------------
# REDIS CONNECTION
# ---------------------------------------------------------
def get_redis_connection():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
    )


# Create shared Redis connection
redis_conn = get_redis_connection()


# ---------------------------------------------------------
# QUEUE
# ---------------------------------------------------------
task_queue = Queue("default", connection=redis_conn)