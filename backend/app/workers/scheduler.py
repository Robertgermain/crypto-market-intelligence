from datetime import datetime, timedelta, timezone

from rq_scheduler import Scheduler
from redis import Redis

from app.core.config import settings
from app.workers.pipeline import run_pipeline


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

    start_time = datetime.now(timezone.utc) + timedelta(seconds=2)

    # -----------------------------------
    # Clear old jobs
    # -----------------------------------
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    print("[INFO] Cleared old scheduled jobs")

    # -----------------------------------
    # Schedule FULL pipeline (every 60s)
    # -----------------------------------
    scheduler.schedule(
        scheduled_time=start_time,
        func=run_pipeline,
        interval=60,
        repeat=None,
        id="market_pipeline"
    )

    print("[INFO] Pipeline scheduled successfully")

    # Keep alive
    while True:
        pass


if __name__ == "__main__":
    main()