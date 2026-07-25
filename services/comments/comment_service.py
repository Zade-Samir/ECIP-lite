"""
Comment Service — Manages inline code annotations, discussion threads, and resolutions.
"""
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.workspaces.team_workspace_manager import TeamWorkspaceManager, WorkspaceRole

logger = get_logger(__name__)


class CommentService:
    """
    Service for persisting and managing code comments and inline annotations.
    """

    def __init__(self, db_path: str = "data/comments.db", workspace_manager: Optional[TeamWorkspaceManager] = None):
        self.db_path = db_path
        self.workspace_manager = workspace_manager
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    text TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.commit()

    def add_comment(
        self,
        workspace_id: str,
        author_id: str,
        file_path: str,
        text: str,
        line_number: Optional[int] = None
    ) -> Optional[int]:
        if self.workspace_manager:
            role = self.workspace_manager.get_role(workspace_id, author_id)
            if not role:
                logger.error("Permission denied")
                return None
            if role == WorkspaceRole.VIEWER.value:
                logger.warning("Read-only access")
                logger.error("Permission denied")
                return None

        try:
            with self._lock:
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO comments (workspace_id, author_id, file_path, line_number, text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (workspace_id, author_id, file_path, line_number, text)
                )
                self._conn.commit()
                comment_id = cursor.lastrowid
            logger.info("Comment added")
            return comment_id
        except Exception:
            logger.error("Collaboration failure")
            return None

    def list_comments(self, workspace_id: str, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT id, workspace_id, author_id, file_path, line_number, text, resolved, created_at FROM comments WHERE workspace_id = ?"
        params = [workspace_id]
        if file_path:
            query += " AND file_path = ?"
            params.append(file_path)

        query += " ORDER BY id ASC"

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        res = []
        for r in rows:
            res.append({
                "id": r[0],
                "workspace_id": r[1],
                "author_id": r[2],
                "file_path": r[3],
                "line_number": r[4],
                "text": r[5],
                "resolved": bool(r[6]),
                "created_at": r[7],
            })
        return res

    def resolve_comment(self, comment_id: int, user_id: str) -> bool:
        try:
            with self._lock:
                self._conn.execute(
                    "UPDATE comments SET resolved = 1 WHERE id = ?",
                    (comment_id,)
                )
                self._conn.commit()
            return True
        except Exception:
            logger.error("Collaboration failure")
            return False
