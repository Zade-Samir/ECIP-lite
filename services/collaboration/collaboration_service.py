"""
Collaboration Service — High-level team activities, saved searches, and presence tracking.
"""
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class CollaborationService:
    """
    Manages team activities, shared saved searches, and live presence.
    """

    def __init__(self, db_path: str = "data/collaboration.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._presence: Dict[str, Dict[str, float]] = {}  # workspace_id -> {user_id: timestamp}
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    query_params TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS activity_feed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.commit()

    def save_search(self, workspace_id: str, user_id: str, name: str, query_params: Dict[str, Any]) -> bool:
        try:
            with self._lock:
                self._conn.execute(
                    """
                    INSERT INTO saved_searches (workspace_id, user_id, name, query_params)
                    VALUES (?, ?, ?, ?)
                    """,
                    (workspace_id, user_id, name, json.dumps(query_params))
                )
                self._conn.commit()
            return True
        except Exception:
            logger.error("Collaboration failure")
            return False

    def get_saved_searches(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, user_id, name, query_params, created_at FROM saved_searches WHERE workspace_id = ?",
                (workspace_id,)
            )
            rows = cursor.fetchall()

        res = []
        for r in rows:
            res.append({
                "id": r[0],
                "user_id": r[1],
                "name": r[2],
                "query_params": json.loads(r[3]),
                "created_at": r[4],
            })
        return res

    def record_activity(self, workspace_id: str, user_id: str, action: str, details: str = "") -> bool:
        try:
            with self._lock:
                self._conn.execute(
                    "INSERT INTO activity_feed (workspace_id, user_id, action, details) VALUES (?, ?, ?, ?)",
                    (workspace_id, user_id, action, details)
                )
                self._conn.commit()
            return True
        except Exception:
            logger.error("Collaboration failure")
            return False

    def get_activity_feed(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, user_id, action, details, created_at FROM activity_feed WHERE workspace_id = ? ORDER BY id DESC LIMIT ?",
                (workspace_id, limit)
            )
            rows = cursor.fetchall()

        return [
            {"id": r[0], "user_id": r[1], "action": r[2], "details": r[3], "created_at": r[4]}
            for r in rows
        ]

    def update_presence(self, workspace_id: str, user_id: str) -> None:
        with self._lock:
            if workspace_id not in self._presence:
                self._presence[workspace_id] = {}
            self._presence[workspace_id][user_id] = time.time()

    def get_active_presence(self, workspace_id: str, timeout_seconds: float = 300.0) -> List[str]:
        cutoff = time.time() - timeout_seconds
        with self._lock:
            ws_p = self._presence.get(workspace_id, {})
            return [uid for uid, ts in ws_p.items() if ts >= cutoff]
