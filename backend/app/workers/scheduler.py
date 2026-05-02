from datetime import datetime, timedelta, timezone

from rq_scheduler import Scheduler
from redis import Redis

from app.core.config import settings
from app.workers.tasks import process_price_data


def get_redis_connection():
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
    )


def main():
    redis_conn = get_redis_connection()
    scheduler = Scheduler(connection=redis_conn)

    print("[INFO] Scheduler started...")

    start_time = datetime.now(timezone.utc) + timedelta(seconds=1)

    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    print("[INFO] Cleared old scheduled jobs")

    # -----------------------------------
    # Schedule Bitcoin
    # -----------------------------------
    scheduler.schedule(
        scheduled_time=start_time,
        func=process_price_data,
        args=[1],
        interval=30,
        repeat=None,
        id="scheduler_bitcoin"
    )

    # -----------------------------------
    # Schedule Ethereum
    # -----------------------------------
    scheduler.schedule(
        scheduled_time=start_time,
        func=process_price_data,
        args=[2],
        interval=30,
        repeat=None,
        id="scheduler_ethereum"
    )

    print("[INFO] Jobs scheduled successfully")

    # Keep process alive
    while True:
        pass


if __name__ == "__main__":
    main()