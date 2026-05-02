import time

from app.core.redis import task_queue
from app.workers.tasks import process_price_data


def enqueue_test_jobs(asset_ids=None, delay: int = 5):
    """
    Enqueue test jobs for multiple assets with delay and basic deduplication
    """

    if asset_ids is None:
        asset_ids = [1, 2]  # bitcoin, ethereum

    print(f"[INFO] Enqueuing jobs for assets: {asset_ids}")

    for asset_id in asset_ids:

        job_id = f"process_price_data_{asset_id}"

        try:
            existing_job = task_queue.fetch_job(job_id)

            if existing_job:
                print(f"[SKIP] Job already exists for asset {asset_id} → {job_id}")
                continue

            # -----------------------------------
            # Enqueue job
            # -----------------------------------
            job = task_queue.enqueue(
                process_price_data,
                asset_id,
                job_id=job_id
            )

            print(f"[ENQUEUED] Asset {asset_id} → Job ID: {job.id}")

        except Exception as e:
            print(f"[ERROR] Failed to enqueue asset {asset_id}: {e}")
            continue

        # -----------------------------------
        # Delay to avoid API rate limiting
        # -----------------------------------
        print(f"[WAIT] Sleeping for {delay} seconds...\n")
        time.sleep(delay)

    print("[DONE] All jobs enqueued")


if __name__ == "__main__":
    enqueue_test_jobs()