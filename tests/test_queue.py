"""
Tests for JobQueue (Prompt 068).
"""
import time
import threading
import pytest
from services.queue.job_queue import JobQueue, TaskStatus


class TestJobQueueBasic:
    def test_enqueue_and_dequeue(self):
        q = JobQueue()
        q.enqueue("task1", lambda: None)
        task = q.dequeue(timeout=0.5)
        assert task is not None
        assert task.name == "task1"

    def test_dequeue_empty_returns_none(self):
        q = JobQueue()
        task = q.dequeue(timeout=0.1)
        assert task is None

    def test_qsize(self):
        q = JobQueue()
        q.enqueue("a", lambda: None)
        q.enqueue("b", lambda: None)
        assert q.qsize() == 2

    def test_stats_enqueued(self):
        q = JobQueue()
        q.enqueue("s1", lambda: None)
        q.enqueue("s2", lambda: None)
        stats = q.stats()
        assert stats["enqueued"] == 2


class TestJobQueueAckNack:
    def test_ack_marks_complete(self):
        q = JobQueue()
        q.enqueue("t1", lambda: None)
        task = q.dequeue(timeout=0.5)
        assert task is not None
        result = q.ack(task.task_id)
        assert result is True
        assert q.in_flight_count() == 0

    def test_nack_requeues_on_retry(self):
        q = JobQueue()
        q.enqueue("t2", lambda: None, max_retries=2)
        task = q.dequeue(timeout=0.5)
        q.nack(task.task_id)
        # Task should be back in queue
        assert q.qsize() == 1

    def test_nack_dead_letter_on_exhaustion(self):
        q = JobQueue()
        q.enqueue("t3", lambda: None, max_retries=0)
        task = q.dequeue(timeout=0.5)
        q.nack(task.task_id)  # First nack = retry_count 1 > max_retries 0
        assert q.dead_letter_count() == 1

    def test_in_flight_tracking(self):
        q = JobQueue()
        q.enqueue("t4", lambda: None)
        task = q.dequeue(timeout=0.5)
        assert q.in_flight_count() == 1
        q.ack(task.task_id)
        assert q.in_flight_count() == 0


class TestJobQueuePriority:
    def test_higher_priority_dequeued_first(self):
        q = JobQueue()
        q.enqueue("low", lambda: None, priority=4)
        q.enqueue("high", lambda: None, priority=1)
        first = q.dequeue(timeout=0.5)
        assert first.name == "high"

    def test_multiple_priority_ordering(self):
        q = JobQueue()
        q.enqueue("normal", lambda: None, priority=3)
        q.enqueue("critical", lambda: None, priority=1)
        q.enqueue("low", lambda: None, priority=4)

        first = q.dequeue(timeout=0.5)
        assert first.name == "critical"


class TestJobQueueConcurrency:
    def test_concurrent_enqueue_dequeue(self):
        q = JobQueue()
        results = []
        lock = threading.Lock()

        def producer():
            for i in range(10):
                q.enqueue(f"task-{i}", lambda i=i: (lock.acquire(), results.append(i), lock.release()))
                time.sleep(0.01)

        def consumer():
            for _ in range(10):
                task = q.dequeue(timeout=1.0)
                if task:
                    task.fn()
                    q.ack(task.task_id)

        t1 = threading.Thread(target=producer)
        t2 = threading.Thread(target=consumer)
        t1.start()
        t2.start()
        t1.join(timeout=3)
        t2.join(timeout=3)

        assert len(results) == 10
