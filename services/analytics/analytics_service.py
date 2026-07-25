"""
Analytics Service — SQLite-backed privacy-aware usage event collection and retention.
"""
import datetime
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from ecip_core.metrics.privacy_filter import PrivacyFilter

logger = get_logger(__name__)


class AnalyticsService:
    """
    Collects and stores privacy-filtered usage analytics events.
    """

    def __init__(self, db_path: str = "data/analytics.db", enabled: bool = True):
        self.enabled = enabled
        self.db_path = db_path
        self._lock = threading.Lock()

        if self.enabled:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    latency_ms REAL DEFAULT 0.0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.commit()

    def record_event(
        self,
        tenant_id: str,
        user_id: str,
        domain: str,
        event_type: str,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not self.enabled:
            logger.warning("Analytics disabled")
            return False

        safe_metadata = PrivacyFilter.sanitize(metadata or {})
        try:
            with self._lock:
                self._conn.execute(
                    """
                    INSERT INTO usage_events (tenant_id, user_id, domain, event_type, latency_ms, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (tenant_id, user_id, domain, event_type, latency_ms, json.dumps(safe_metadata)),
                )
                self._conn.commit()
            logger.info("Event recorded")
            return True
        except Exception as e:
            return False

    def get_events(
        self,
        tenant_id: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        if not self.enabled:
            logger.warning("Analytics disabled")
            return []

        query = "SELECT tenant_id, user_id, domain, event_type, latency_ms, metadata, created_at FROM usage_events"
        params = []
        conditions = []

        if tenant_id:
            conditions.append("tenant_id = ?")
            params.append(tenant_id)
        if domain:
            conditions.append("domain = ?")
            params.append(domain)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        events = []
        for r in rows:
            events.append({
                "tenant_id": r[0],
                "user_id": r[1],
                "domain": r[2],
                "event_type": r[3],
                "latency_ms": r[4],
                "metadata": json.loads(r[5]) if r[5] else {},
                "created_at": r[6],
            })
        return events

    def apply_retention(self, days: int = 30) -> int:
        if not self.enabled:
            logger.warning("Analytics disabled")
            return 0

        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM usage_events WHERE created_at < ?", (cutoff,))
            deleted = cursor.rowcount
            self._conn.commit()

        logger.warning("Retention cleanup")
        return deleted
