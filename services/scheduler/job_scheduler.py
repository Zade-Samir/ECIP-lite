"""
Job Scheduler — Thread-based scheduler for ECIP background jobs.
Supports: interval scheduling, one-shot jobs, priority ordering,
retry with exponential backoff, and graceful shutdown.
Local-only: uses Python threading + PriorityQueue.
"""
import time
import uuid
import heapq
import threading
import traceback
import datetime
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, field

from ecip_core.common.logger import get_logger
from services.scheduler.job_history import JobHistory, JobStatus

logger = get_logger(__name__)


class JobPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass(order=True)
class ScheduledJob:
    """A job queued for execution."""
    run_at: float                             # Unix timestamp for next run
    priority: int                             # Lower = higher priority
    job_id: str = field(compare=False)
    name: str = field(compare=False)
    fn: Callable = field(compare=False)
    args: tuple = field(compare=False, default_factory=tuple)
    kwargs: dict = field(compare=False, default_factory=dict)
    interval_seconds: Optional[float] = field(compare=False, default=None)  # None = one-shot
    max_retries: int = field(compare=False, default=3)
    retry_count: int = field(compare=False, default=0)
    retry_delay: float = field(compare=False, default=5.0)  # Base delay for exponential backoff


class JobScheduler:
    """
    Lightweight in-process job scheduler.

    Usage:
        scheduler = JobScheduler()
        scheduler.start()

        # One-shot job
        scheduler.schedule_once("my_job", my_fn, delay_seconds=10)

        # Recurring job every 5 minutes
        scheduler.schedule_interval("cleanup", cleanup_fn, interval_seconds=300)

        # Graceful shutdown
        scheduler.stop()
    """

    def __init__(self, history: Optional[JobHistory] = None):
        self._heap: list[ScheduledJob] = []
        self._heap_lock = threading.Lock()
        self._cond = threading.Condition(self._heap_lock)
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._history = history or JobHistory()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the scheduler worker thread."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._run_loop, daemon=True, name="ecip-scheduler"
        )
        self._worker_thread.start()
        logger.info("Job scheduled")

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the scheduler gracefully."""
        self._running = False
        with self._cond:
            self._cond.notify_all()
        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)

    def schedule_once(
        self,
        name: str,
        fn: Callable,
        delay_seconds: float = 0,
        args: tuple = (),
        kwargs: dict = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
    ) -> str:
        """Schedule a job to run once after delay_seconds."""
        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            run_at=time.monotonic() + delay_seconds,
            priority=priority.value,
            job_id=job_id,
            name=name,
            fn=fn,
            args=args,
            kwargs=kwargs or {},
            interval_seconds=None,
            max_retries=max_retries,
        )
        self._enqueue(job)
        logger.info("Job scheduled")
        return job_id

    def schedule_interval(
        self,
        name: str,
        fn: Callable,
        interval_seconds: float,
        args: tuple = (),
        kwargs: dict = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        run_immediately: bool = False,
    ) -> str:
        """Schedule a recurring job at a fixed interval."""
        job_id = str(uuid.uuid4())
        delay = 0 if run_immediately else interval_seconds
        job = ScheduledJob(
            run_at=time.monotonic() + delay,
            priority=priority.value,
            job_id=job_id,
            name=name,
            fn=fn,
            args=args,
            kwargs=kwargs or {},
            interval_seconds=interval_seconds,
            max_retries=max_retries,
        )
        self._enqueue(job)
        logger.info("Job scheduled")
        return job_id

    def cancel(self, job_id: str) -> bool:
        """Cancel a scheduled job by ID (marks as cancelled in heap)."""
        with self._cond:
            for job in self._heap:
                if job.job_id == job_id:
                    job.fn = lambda *a, **kw: None  # Neutralise
                    job.interval_seconds = None
                    return True
        return False

    def pending_count(self) -> int:
        with self._heap_lock:
            return len(self._heap)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _enqueue(self, job: ScheduledJob) -> None:
        with self._cond:
            heapq.heappush(self._heap, job)
            self._cond.notify()

    def _run_loop(self) -> None:
        while self._running:
            with self._cond:
                # Wait if heap is empty
                while self._running and not self._heap:
                    self._cond.wait(timeout=1.0)

                if not self._running:
                    break

                now = time.monotonic()
                if self._heap[0].run_at > now:
                    wait = self._heap[0].run_at - now
                    self._cond.wait(timeout=min(wait, 1.0))
                    continue

                job = heapq.heappop(self._heap)

            # Execute outside lock
            self._execute(job)

    def _execute(self, job: ScheduledJob) -> None:
        logger.info("Job started")
        exec_id = str(uuid.uuid4())
        self._history.record_start(exec_id, job.job_id, job.name)

        try:
            job.fn(*job.args, **job.kwargs)
            self._history.record_success(exec_id)
            logger.info("Job completed")

            # Re-schedule if recurring
            if job.interval_seconds:
                next_job = ScheduledJob(
                    run_at=time.monotonic() + job.interval_seconds,
                    priority=job.priority,
                    job_id=job.job_id,
                    name=job.name,
                    fn=job.fn,
                    args=job.args,
                    kwargs=job.kwargs,
                    interval_seconds=job.interval_seconds,
                    max_retries=job.max_retries,
                    retry_count=0,
                )
                self._enqueue(next_job)

        except Exception as e:
            logger.error("Job failed")
            error_msg = traceback.format_exc()
            self._history.record_failure(exec_id, error_msg)

            if job.retry_count < job.max_retries:
                backoff = job.retry_delay * (2 ** job.retry_count)
                logger.warning("Retry scheduled")
                retry_job = ScheduledJob(
                    run_at=time.monotonic() + backoff,
                    priority=job.priority,
                    job_id=job.job_id,
                    name=job.name,
                    fn=job.fn,
                    args=job.args,
                    kwargs=job.kwargs,
                    interval_seconds=job.interval_seconds,
                    max_retries=job.max_retries,
                    retry_count=job.retry_count + 1,
                    retry_delay=job.retry_delay,
                )
                self._enqueue(retry_job)
