import time
import json
import threading
from pathlib import Path
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

from ecip_core.logging import get_logger
from ecip_core.logging.correlation import get_correlation_id

logger = get_logger(__name__)


class MetricsCollector:
    """
    Central performance measurement framework for ECIP Lite.
    Tracks named and nested timers, compiles aggregated statistics,
    and supports exporting metrics to JSON format.
    
    Thread-safe and supports concurrent requests using correlation IDs.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern wrapper."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_collector()
            return cls._instance

    def _init_collector(self):
        # Maps correlation_id -> timer_name -> list of start timestamps (stack for nesting)
        self._active_timers: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        # Maps correlation_id -> timer_name -> list of completed elapsed times in milliseconds
        self._completed_runs: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self._global_lock = threading.Lock()

    def start_timer(self, name: str) -> None:
        """Start a named timer under the current correlation context."""
        cid = get_correlation_id()
        t_start = time.perf_counter()

        with self._global_lock:
            self._active_timers[cid][name].append(t_start)

        logger.info(f"Timer started: {name} [CID:{cid}]")

    def stop_timer(self, name: str) -> Optional[float]:
        """Stop a named timer, record elapsed duration in ms, and return it."""
        cid = get_correlation_id()
        t_stop = time.perf_counter()

        with self._global_lock:
            stack = self._active_timers[cid].get(name)
            if not stack:
                logger.warning(f"Missing metric: Attempted to stop timer '{name}' which was not started [CID:{cid}].")
                return None

            t_start = stack.pop()
            # Clean up empty list to save space
            if not stack:
                del self._active_timers[cid][name]

            elapsed_ms = (t_stop - t_start) * 1000
            self._completed_runs[cid][name].append(elapsed_ms)

        logger.info(f"Timer stopped: {name} | dur:{elapsed_ms:.2f}ms [CID:{cid}]")
        return elapsed_ms

    def record_duration(self, name: str, duration_ms: float) -> None:
        """Manually record an externally-timed duration in ms."""
        cid = get_correlation_id()
        with self._global_lock:
            self._completed_runs[cid][name].append(duration_ms)
        logger.info(f"Timer recorded: {name} | dur:{duration_ms:.2f}ms [CID:{cid}]")

    @contextmanager
    def timer(self, name: str):
        """Context manager utility to automatically time execution blocks."""
        self.start_timer(name)
        try:
            yield
        finally:
            self.stop_timer(name)

    def get_stats(self, name: str, cid: Optional[str] = None) -> Dict[str, Any]:
        """
        Compiles aggregated metrics stats (count, total, average, min, max)
        for a specific timer. If cid is provided, returns stats isolated to that request.
        """
        durations = []
        with self._global_lock:
            if cid is not None:
                durations = self._completed_runs.get(cid, {}).get(name, [])
            else:
                # Aggregate across all correlation IDs/runs
                for cid_runs in self._completed_runs.values():
                    durations.extend(cid_runs.get(name, []))

        if not durations:
            return {
                "metric": name,
                "count": 0,
                "total_ms": 0.0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
            }

        return {
            "metric": name,
            "count": len(durations),
            "total_ms": round(sum(durations), 4),
            "avg_ms": round(sum(durations) / len(durations), 4),
            "min_ms": round(min(durations), 4),
            "max_ms": round(max(durations), 4),
        }

    def get_all_stats(self, cid: Optional[str] = None) -> List[Dict[str, Any]]:
        """Compiles stats for all recorded timers."""
        metrics_names = set()
        with self._global_lock:
            if cid is not None:
                metrics_names.update(self._completed_runs.get(cid, {}).keys())
            else:
                for cid_runs in self._completed_runs.values():
                    metrics_names.update(cid_runs.keys())

        # Sort alphabetically for deterministic output
        stats = []
        for name in sorted(metrics_names):
            stats.append(self.get_stats(name, cid=cid))
        return stats

    def export_json(self, file_path: Optional[str] = None, cid: Optional[str] = None) -> str:
        """
        Serializes aggregated metrics to a JSON string and optionally writes it to a file.
        """
        try:
            report_data = {
                "active_profile": self._get_active_profile(),
                "metrics": self.get_all_stats(cid=cid)
            }
            json_str = json.dumps(report_data, indent=2)

            if file_path:
                dest = Path(file_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json_str, encoding="utf-8")
                logger.info(f"Metrics exported to {file_path}")

            return json_str
        except Exception as e:
            logger.error(f"Metrics export failure: {e}")
            raise

    def clear(self) -> None:
        """Resets all metrics state."""
        with self._global_lock:
            self._active_timers.clear()
            self._completed_runs.clear()

    def _get_active_profile(self) -> str:
        try:
            from ecip_core.settings import settings
            return settings.ECIP_PROFILE
        except Exception:
            return "unknown"


# Global singleton instance
metrics_collector = MetricsCollector()
