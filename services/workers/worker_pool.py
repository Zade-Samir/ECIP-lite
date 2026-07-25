"""
Worker Pool — Thread-based local distributed worker architecture.
Uses ThreadPoolExecutor with heartbeat monitoring and task leasing.
"""
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Callable, Dict

from ecip_core.common.logger import get_logger
from services.queue.job_queue import JobQueue, Task

logger = get_logger(__name__)


class WorkerInfo:
    """Tracks state of an individual worker."""
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.registered_at = time.monotonic()
        self.last_heartbeat = time.monotonic()
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.current_task: Optional[str] = None
        self.is_alive = True

    def heartbeat(self) -> None:
        self.last_heartbeat = time.monotonic()

    def is_stale(self, timeout: float = 30.0) -> bool:
        return (time.monotonic() - self.last_heartbeat) > timeout


class WorkerPool:
    """
    Manages a pool of worker threads that drain a JobQueue.

    Features:
    - Configurable concurrency (thread count)
    - Worker heartbeat monitoring
    - Automatic retry via JobQueue.nack()
    - Graceful shutdown with task drain

    Usage:
        q = JobQueue()
        pool = WorkerPool(queue=q, num_workers=4)
        pool.start()
        q.enqueue("my_task", my_fn)
        pool.stop()
    """

    def __init__(
        self,
        queue: Optional[JobQueue] = None,
        num_workers: int = 4,
        heartbeat_interval: float = 5.0,
        worker_timeout: float = 30.0,
    ):
        self.queue = queue or JobQueue()
        self.num_workers = num_workers
        self.heartbeat_interval = heartbeat_interval
        self.worker_timeout = worker_timeout

        self._executor: Optional[ThreadPoolExecutor] = None
        self._workers: Dict[str, WorkerInfo] = {}
        self._lock = threading.Lock()
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._drain_threads: list[threading.Thread] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the worker pool and heartbeat monitor."""
        if self._running:
            return
        self._running = True
        self._executor = ThreadPoolExecutor(
            max_workers=self.num_workers,
            thread_name_prefix="ecip-worker"
        )

        # Register workers
        for i in range(self.num_workers):
            worker_id = f"worker-{uuid.uuid4().hex[:8]}"
            info = WorkerInfo(worker_id)
            with self._lock:
                self._workers[worker_id] = info
            logger.info("Worker registered")

            t = threading.Thread(
                target=self._drain_worker,
                args=(worker_id,),
                daemon=True,
                name=f"ecip-drainer-{i}"
            )
            t.start()
            self._drain_threads.append(t)

        # Start heartbeat monitor
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_monitor, daemon=True, name="ecip-heartbeat"
        )
        self._heartbeat_thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the worker pool gracefully."""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def active_workers(self) -> list[dict]:
        """Return info on all active workers."""
        with self._lock:
            return [
                {
                    "worker_id": w.worker_id,
                    "is_alive": w.is_alive,
                    "tasks_completed": w.tasks_completed,
                    "tasks_failed": w.tasks_failed,
                    "current_task": w.current_task,
                    "last_heartbeat_age": round(time.monotonic() - w.last_heartbeat, 2),
                }
                for w in self._workers.values()
            ]

    def stats(self) -> dict:
        with self._lock:
            return {
                "total_workers": len(self._workers),
                "alive_workers": sum(1 for w in self._workers.values() if w.is_alive),
                "queue_size": self.queue.qsize(),
                "in_flight": self.queue.in_flight_count(),
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _drain_worker(self, worker_id: str) -> None:
        """Worker loop: dequeue and execute tasks."""
        while self._running:
            task = self.queue.dequeue(timeout=0.5)
            if task is None:
                with self._lock:
                    if worker_id in self._workers:
                        self._workers[worker_id].heartbeat()
                continue

            with self._lock:
                if worker_id in self._workers:
                    self._workers[worker_id].current_task = task.task_id
                    self._workers[worker_id].heartbeat()

            try:
                task.fn(*task.args, **task.kwargs)
                self.queue.ack(task.task_id)
                with self._lock:
                    if worker_id in self._workers:
                        self._workers[worker_id].tasks_completed += 1
                        self._workers[worker_id].current_task = None
            except Exception as e:
                logger.error("Worker offline")
                self.queue.nack(task.task_id)
                with self._lock:
                    if worker_id in self._workers:
                        self._workers[worker_id].tasks_failed += 1
                        self._workers[worker_id].current_task = None

    def _heartbeat_monitor(self) -> None:
        """Monitor for stale/dead workers and log warnings."""
        while self._running:
            time.sleep(self.heartbeat_interval)
            with self._lock:
                for worker in self._workers.values():
                    if worker.is_stale(self.worker_timeout):
                        logger.warning("Heartbeat delayed")
                        worker.is_alive = False
