"""
Job Queue — Priority queue abstraction for distributed worker tasks.
Uses Python's queue.PriorityQueue. Supports task acknowledgement and retry.
"""
import uuid
import time
import queue
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass(order=True)
class Task:
    """A unit of work in the job queue."""
    priority: int                              # Lower = higher priority
    task_id: str = field(compare=False)
    name: str = field(compare=False)
    fn: Callable = field(compare=False)
    args: tuple = field(compare=False, default_factory=tuple)
    kwargs: dict = field(compare=False, default_factory=dict)
    max_retries: int = field(compare=False, default=3)
    retry_count: int = field(compare=False, default=0)
    enqueued_at: float = field(compare=False, default_factory=time.monotonic)


class JobQueue:
    """
    Thread-safe priority job queue with acknowledgement and retry support.

    Usage:
        q = JobQueue()
        task_id = q.enqueue("my_task", my_fn, priority=2)
        task = q.dequeue(timeout=1.0)
        if task:
            try:
                task.fn()
                q.ack(task.task_id)
            except Exception:
                q.nack(task.task_id)
    """

    def __init__(self, maxsize: int = 0):
        self._queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=maxsize)
        self._in_flight: dict[str, Task] = {}
        self._dead_letter: list[Task] = []
        self._lock = threading.Lock()
        self._stats = {"enqueued": 0, "completed": 0, "failed": 0}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(
        self,
        name: str,
        fn: Callable,
        priority: int = 3,
        args: tuple = (),
        kwargs: dict = None,
        max_retries: int = 3,
    ) -> str:
        """Add a task to the queue. Returns task_id."""
        task_id = str(uuid.uuid4())
        task = Task(
            priority=priority,
            task_id=task_id,
            name=name,
            fn=fn,
            args=args,
            kwargs=kwargs or {},
            max_retries=max_retries,
        )
        self._queue.put(task)
        with self._lock:
            self._stats["enqueued"] += 1
        logger.info("Job assigned")
        return task_id

    def dequeue(self, timeout: float = 1.0) -> Optional[Task]:
        """
        Dequeue the highest-priority task.
        Moves task to in-flight tracking until ack/nack.
        Returns None if queue is empty within timeout.
        """
        try:
            task = self._queue.get(timeout=timeout)
            with self._lock:
                self._in_flight[task.task_id] = task
            return task
        except queue.Empty:
            return None

    def ack(self, task_id: str) -> bool:
        """Acknowledge successful task completion."""
        with self._lock:
            task = self._in_flight.pop(task_id, None)
            if task:
                self._stats["completed"] += 1
                logger.info("Job completed")
                return True
        logger.warning("Worker overloaded")
        return False

    def nack(self, task_id: str) -> bool:
        """
        Negative-acknowledge a failed task.
        Re-queues if max_retries not exhausted, else sends to dead-letter queue.
        """
        with self._lock:
            task = self._in_flight.pop(task_id, None)
            if not task:
                return False

            task.retry_count += 1
            if task.retry_count <= task.max_retries:
                logger.warning("Heartbeat delayed")
            else:
                self._dead_letter.append(task)
                self._stats["failed"] += 1
                logger.error("Task lost")
                return True

        # Re-enqueue outside lock
        if task.retry_count <= task.max_retries:
            self._queue.put(task)
        return True

    def qsize(self) -> int:
        return self._queue.qsize()

    def in_flight_count(self) -> int:
        with self._lock:
            return len(self._in_flight)

    def dead_letter_count(self) -> int:
        with self._lock:
            return len(self._dead_letter)

    def get_dead_letter(self) -> list[Task]:
        with self._lock:
            return list(self._dead_letter)

    def stats(self) -> dict:
        with self._lock:
            return dict(self._stats)
