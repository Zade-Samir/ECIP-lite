"""
Tests for WorkerPool (Prompt 068).
"""
import time
import threading
import pytest
from services.queue.job_queue import JobQueue
from services.workers.worker_pool import WorkerPool


@pytest.fixture
def queue():
    return JobQueue()


@pytest.fixture
def pool(queue):
    p = WorkerPool(queue=queue, num_workers=2, heartbeat_interval=60)
    p.start()
    yield p
    p.stop()


class TestWorkerPoolExecution:
    def test_task_executed_by_pool(self, pool, queue):
        results = []
        queue.enqueue("task1", lambda: results.append(1))
        time.sleep(0.5)
        assert results == [1]

    def test_multiple_tasks_executed(self, pool, queue):
        results = []
        lock = threading.Lock()
        for i in range(5):
            queue.enqueue("multi", lambda i=i: (lock.acquire(), results.append(i), lock.release()))
        time.sleep(1.0)
        assert len(results) == 5

    def test_active_workers_reported(self, pool):
        workers = pool.active_workers()
        assert len(workers) == 2

    def test_stats_reflect_queue(self, pool, queue):
        stats = pool.stats()
        assert stats["total_workers"] == 2
        assert stats["queue_size"] == 0


class TestWorkerPoolRetry:
    def test_failed_task_requeued(self, pool, queue):
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ValueError("Temporary failure")

        queue.enqueue("flaky", flaky, max_retries=3)
        time.sleep(1.0)
        assert call_count["n"] >= 2

    def test_dead_letter_on_exhausted_retries(self, queue):
        """Tasks that fail beyond max_retries end up in dead-letter queue."""
        pool = WorkerPool(queue=queue, num_workers=1)
        pool.start()

        queue.enqueue("always_fail", lambda: (_ for _ in ()).throw(Exception("fail")), max_retries=0)
        time.sleep(0.5)
        pool.stop()

        assert queue.dead_letter_count() >= 1


class TestWorkerPoolGracefulShutdown:
    def test_stop_does_not_raise(self, queue):
        pool = WorkerPool(queue=queue, num_workers=2)
        pool.start()
        pool.stop()  # Should not raise
