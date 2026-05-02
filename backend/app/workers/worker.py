import redis
from rq import Worker, Queue

from app.core.config import settings


def get_redis_connection():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
    )


def main():
    redis_conn = get_redis_connection()
    queue = Queue("default", connection=redis_conn)

    worker = Worker(
        [queue],
        connection=redis_conn,
        disable_default_exception_handler=False
    )

    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()