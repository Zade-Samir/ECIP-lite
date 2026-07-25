"""
Worker Registry — tracks all registered workers across the pool.
"""
import time
import threading
from typing import Dict, Optional
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class WorkerRegistry:
    """
    Global registry of active workers. Thread-safe.

    Workers register themselves on startup and deregister on shutdown.
    The registry can detect offline workers via heartbeat staleness.
    """

    def __init__(self, stale_timeout: float = 30.0):
        self._workers: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self.stale_timeout = stale_timeout

    def register(self, worker_id: str, metadata: dict = None) -> None:
        with self._lock:
            self._workers[worker_id] = {
                "worker_id": worker_id,
                "registered_at": time.time(),
                "last_heartbeat": time.time(),
                "status": "idle",
                **(metadata or {}),
            }
        logger.info("Worker registered")

    def deregister(self, worker_id: str) -> bool:
        with self._lock:
            return bool(self._workers.pop(worker_id, None))

    def heartbeat(self, worker_id: str, status: str = "idle") -> bool:
        with self._lock:
            if worker_id in self._workers:
                self._workers[worker_id]["last_heartbeat"] = time.time()
                self._workers[worker_id]["status"] = status
                return True
        return False

    def get(self, worker_id: str) -> Optional[dict]:
        with self._lock:
            return dict(self._workers.get(worker_id, {}))

    def list_workers(self) -> list[dict]:
        with self._lock:
            return [dict(w) for w in self._workers.values()]

    def list_alive(self) -> list[dict]:
        cutoff = time.time() - self.stale_timeout
        with self._lock:
            return [
                dict(w) for w in self._workers.values()
                if w["last_heartbeat"] >= cutoff
            ]

    def list_stale(self) -> list[dict]:
        cutoff = time.time() - self.stale_timeout
        with self._lock:
            return [
                dict(w) for w in self._workers.values()
                if w["last_heartbeat"] < cutoff
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._workers)
