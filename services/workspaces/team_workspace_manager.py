"""
Team Workspace Manager — Manages shared team workspaces, roles, and member invitations.
"""
from enum import Enum
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class WorkspaceRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"


class TeamWorkspaceManager:
    """
    Manages team workspaces, membership, roles, and ownership transfers.
    """

    def __init__(self, db_path: str = "data/team_workspaces.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS workspace_members (
                    workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    PRIMARY KEY (workspace_id, user_id)
                )
            """)
            self._conn.commit()

    def create_workspace(self, workspace_id: str, name: str, owner_id: str) -> bool:
        try:
            with self._lock:
                self._conn.execute(
                    "INSERT INTO workspaces (workspace_id, name, owner_id) VALUES (?, ?, ?)",
                    (workspace_id, name, owner_id)
                )
                self._conn.execute(
                    "INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?, ?, ?)",
                    (workspace_id, owner_id, WorkspaceRole.OWNER.value)
                )
                self._conn.commit()
            logger.info("Workspace created")
            return True
        except Exception as e:
            logger.error("Collaboration failure")
            return False

    def get_role(self, workspace_id: str, user_id: str) -> Optional[str]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT role FROM workspace_members WHERE workspace_id = ? AND user_id = ?",
                (workspace_id, user_id)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def invite_member(
        self,
        workspace_id: str,
        inviter_id: str,
        member_id: str,
        role: str = WorkspaceRole.DEVELOPER.value
    ) -> bool:
        inviter_role = self.get_role(workspace_id, inviter_id)
        if inviter_role not in (WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value):
            logger.error("Permission denied")
            return False

        existing_role = self.get_role(workspace_id, member_id)
        if existing_role is not None:
            logger.warning("Duplicate invitation")
            return False

        try:
            with self._lock:
                self._conn.execute(
                    "INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?, ?, ?)",
                    (workspace_id, member_id, role)
                )
                self._conn.commit()
            logger.info("Member invited")
            return True
        except Exception:
            logger.error("Collaboration failure")
            return False

    def transfer_ownership(self, workspace_id: str, current_owner_id: str, new_owner_id: str) -> bool:
        role = self.get_role(workspace_id, current_owner_id)
        if role != WorkspaceRole.OWNER.value:
            logger.error("Permission denied")
            return False

        new_role = self.get_role(workspace_id, new_owner_id)
        if not new_role:
            logger.error("Collaboration failure")
            return False

        try:
            with self._lock:
                self._conn.execute(
                    "UPDATE workspaces SET owner_id = ? WHERE workspace_id = ?",
                    (new_owner_id, workspace_id)
                )
                self._conn.execute(
                    "UPDATE workspace_members SET role = ? WHERE workspace_id = ? AND user_id = ?",
                    (WorkspaceRole.ADMIN.value, workspace_id, current_owner_id)
                )
                self._conn.execute(
                    "UPDATE workspace_members SET role = ? WHERE workspace_id = ? AND user_id = ?",
                    (WorkspaceRole.OWNER.value, workspace_id, new_owner_id)
                )
                self._conn.commit()
            return True
        except Exception:
            logger.error("Collaboration failure")
            return False

    def list_members(self, workspace_id: str) -> List[Dict[str, str]]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT user_id, role FROM workspace_members WHERE workspace_id = ?",
                (workspace_id,)
            )
            rows = cursor.fetchall()
        return [{"user_id": r[0], "role": r[1]} for r in rows]
