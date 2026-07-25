"""
Backup Scheduler — Thread-based scheduler for automated recurring backups.
Uses Python threading.Timer for lightweight, dependency-free scheduling.
"""
import threading
import datetime
from pathlib import Path
from typing import Optional, Callable

from ecip_core.common.logger import get_logger
from services.backup.backup_manager import BackupManager

logger = get_logger(__name__)


class BackupScheduler:
    """
    Runs automated backups at configurable intervals using a background thread.

    Usage:
        scheduler = BackupScheduler(
            project_root=".",
            backup_dir="backups",
            interval_seconds=3600,  # hourly
            backup_type="full",
        )
        scheduler.start()
        ...
        scheduler.stop()
    """

    def __init__(
        self,
        project_root: str = ".",
        backup_dir: str = "backups",
        interval_seconds: int = 3600,
        backup_type: str = "incremental",
        retention_days: int = 7,
        encryption_key: Optional[bytes] = None,
        on_success: Optional[Callable[[str], None]] = None,
        on_failure: Optional[Callable[[Exception], None]] = None,
    ):
        self.project_root = project_root
        self.backup_type = backup_type
        self.interval_seconds = interval_seconds
        self.manager = BackupManager(
            backup_dir=backup_dir,
            retention_days=retention_days,
            encryption_key=encryption_key,
        )
        self.on_success = on_success
        self.on_failure = on_failure
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the backup scheduler."""
        with self._lock:
            if self._running:
                logger.warning("Backup delayed")
                return
            self._running = True
        self._schedule_next()
        logger.info("Backup started")

    def stop(self) -> None:
        """Stop the backup scheduler gracefully."""
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None

    def run_now(self) -> Optional[str]:
        """Trigger a backup immediately (outside the schedule)."""
        return self._execute_backup()

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _schedule_next(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._timer = threading.Timer(self.interval_seconds, self._tick)
            self._timer.daemon = True
            self._timer.start()

    def _tick(self) -> None:
        """Execute backup and schedule the next run."""
        self._execute_backup()
        self._schedule_next()

    def _execute_backup(self) -> Optional[str]:
        try:
            if self.backup_type == "full":
                path = self.manager.full_backup(self.project_root)
            else:
                path = self.manager.incremental_backup(self.project_root)

            # Apply retention after each backup
            self.manager.apply_retention()

            if self.on_success and path:
                self.on_success(path)

            return path

        except Exception as e:
            logger.error("Backup failed")
            if self.on_failure:
                self.on_failure(e)
            return None
