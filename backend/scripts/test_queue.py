from app.core.redis import task_queue
from app.workers.tasks import process_price_data


def enqueue_test_job():
    job = task_queue.enqueue(process_price_data, 1)
    print(f"Job enqueued: {job.id}")


if __name__ == "__main__":
    enqueue_test_job()