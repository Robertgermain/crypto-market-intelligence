from time import sleep
from typing import List

from sqlalchemy.orm import Session
import redis

from app.core.database import SessionLocal
from app.core.redis import task_queue
from app.core.config import settings
from app.models.asset import Asset
from app.services.market_data_service import ingest_market_data
from app.workers.tasks import process_price_data


def get_redis():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
    )


def _get_symbols(assets: List[Asset]) -> List[str]:
    return [a.symbol for a in assets if a.symbol]


def run_pipeline():
    """
    FULL PIPELINE:
    1) Load assets
    2) Fetch + store fresh prices
    3) Enqueue signal processing jobs (with locking)
    """

    db: Session = SessionLocal()
    redis_conn = get_redis()

    try:
        print("\n[PIPELINE] 🚀 Starting market data ingestion...")

        # -----------------------------------
        # 1. Load assets
        # -----------------------------------
        assets = db.query(Asset).all()

        if not assets:
            print("[PIPELINE][WARN] No assets found in DB")
            return

        symbols = _get_symbols(assets)
        if not symbols:
            print("[PIPELINE][WARN] No valid symbols found")
            return

        print(f"[PIPELINE] Assets loaded: {symbols}")

        # -----------------------------------
        # 2. Fetch + store fresh prices
        # -----------------------------------
        inserted = ingest_market_data(db, symbols)

        if not inserted:
            print("[PIPELINE][WARN] No new market data returned")
        else:
            print(f"[PIPELINE] ✅ Inserted {len(inserted)} price records")

        # -----------------------------------
        # 3. Enqueue signal jobs (WITH LOCK)
        # -----------------------------------
        for asset in assets:
            lock_key = f"lock:process_price_data:{asset.id}"

            # -----------------------------------
            # Skip if recently processed
            # -----------------------------------
            if redis_conn.get(lock_key):
                print(f"[PIPELINE][SKIP] Lock exists for {asset.symbol}")
                continue

            # -----------------------------------
            # Set lock (prevents duplicates)
            # -----------------------------------
            redis_conn.setex(lock_key, 45, "1")  # 45 sec lock

            # -----------------------------------
            # Enqueue job
            # -----------------------------------
            job = task_queue.enqueue(
                process_price_data,
                asset.id,
                job_id=f"process_price_data_{asset.id}",
                result_ttl=300,
                failure_ttl=300,
            )

            print(f"[PIPELINE][ENQUEUED] {asset.symbol} → Job ID: {job.id}")

            # Small delay to avoid API bursts
            sleep(0.3)

    except Exception as e:
        db.rollback()
        print(f"[PIPELINE][ERROR] {e}")

    finally:
        db.close()
        print("[PIPELINE] 🧹 DB session closed")