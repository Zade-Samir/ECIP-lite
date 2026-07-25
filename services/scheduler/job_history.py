"""
Job History — SQLite-backed execution history for scheduled jobs.
Tracks job runs, durations, statuses, and errors.
"""
import sqlite3
import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class JobStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class JobHistory:
    """
    Persists job execution records to SQLite.

    Schema: job_executions(exec_id, job_id, name, status, started_at, ended_at, error)
    """

    def __init__(self, db_path: str = "data/job_history.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._lock = __import__("threading").Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS job_executions (
                exec_id   TEXT PRIMARY KEY,
                job_id    TEXT NOT NULL,
                name      TEXT NOT NULL,
                status    TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at   TEXT,
                error      TEXT
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON job_executions(job_id)")
        self._conn.commit()

    def record_start(self, exec_id: str, job_id: str, name: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO job_executions(exec_id, job_id, name, status, started_at) VALUES (?,?,?,?,?)",
                (exec_id, job_id, name, JobStatus.RUNNING, datetime.datetime.utcnow().isoformat())
            )
            self._conn.commit()

    def record_success(self, exec_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE job_executions SET status=?, ended_at=? WHERE exec_id=?",
                (JobStatus.SUCCESS, datetime.datetime.utcnow().isoformat(), exec_id)
            )
            self._conn.commit()

    def record_failure(self, exec_id: str, error: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE job_executions SET status=?, ended_at=?, error=? WHERE exec_id=?",
                (JobStatus.FAILED, datetime.datetime.utcnow().isoformat(), error[:2000], exec_id)
            )
            self._conn.commit()

    def get_history(self, job_id: Optional[str] = None, limit: int = 50) -> list[dict]:
        with self._lock:
            if job_id:
                rows = self._conn.execute(
                    "SELECT * FROM job_executions WHERE job_id=? ORDER BY started_at DESC LIMIT ?",
                    (job_id, limit)
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM job_executions ORDER BY started_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()

        cols = ["exec_id", "job_id", "name", "status", "started_at", "ended_at", "error"]
        return [dict(zip(cols, row)) for row in rows]

    def get_stats(self) -> dict:
        with self._lock:
            total = self._conn.execute("SELECT COUNT(*) FROM job_executions").fetchone()[0]
            success = self._conn.execute(
                "SELECT COUNT(*) FROM job_executions WHERE status='success'"
            ).fetchone()[0]
            failed = self._conn.execute(
                "SELECT COUNT(*) FROM job_executions WHERE status='failed'"
            ).fetchone()[0]
        return {"total": total, "success": success, "failed": failed}
