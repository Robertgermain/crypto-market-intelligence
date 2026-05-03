from datetime import datetime, timedelta, timezone
from rq_scheduler import Scheduler
from redis import Redis

from app.core.config import settings
from app.workers.tasks import run_full_pipeline


def get_redis_connection():
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
    )


def main():
    redis_conn = get_redis_connection()
    scheduler = Scheduler(connection=redis_conn)

    print("[SCHEDULER] Starting...")

    start_time = datetime.now(timezone.utc) + timedelta(seconds=2)

    # Clear old jobs
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    print("[SCHEDULER] Cleared old jobs")

    # Schedule pipeline
    scheduler.schedule(
        scheduled_time=start_time,
        func=run_full_pipeline,
        interval=60,
        repeat=None,
        id="market_pipeline",
    )

    print("[SCHEDULER] Pipeline scheduled every 60 seconds")

    # Keep alive
    while True:
        pass


if __name__ == "__main__":
    main()