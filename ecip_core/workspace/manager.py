import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import logging

logger = logging.getLogger("ecip.workspace")


class WorkspaceManager:
    """
    Coordinates multi-project workspaces for ECIP Lite.
    Manages workspace registration, selection, deletion, stats,
    and isolates SQLite databases, FAISS indexes, and cache namespaces.
    """

    _instance = None
    _active_project_id = "default"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_active_workspace(cls) -> str:
        """Returns the currently active workspace project_id."""
        return cls._active_project_id

    @classmethod
    def get_active_db_path(cls) -> str:
        """Returns the file path of the database for the active workspace."""
        if cls._active_project_id == "default":
            return "data/ecip.db"
        return f"data/ecip_{cls._active_project_id}.db"

    def _ensure_default_registered(self):
        """Lazily ensures that the default project is registered in the database registry."""
        try:
            from ecip_core.storage.sqlite.database import Database
            # We check registry directly to prevent recursion
            conn = Database.get_registry_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM projects WHERE project_id = 'default'")
            if cursor.fetchone()[0] == 0:
                created_at = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """
                    INSERT INTO projects (
                        project_id, alias, root_path, indexed_at, indexed_files, total_chunks, total_vectors, status
                    ) VALUES ('default', 'Default Workspace', 'projects/default', ?, 0, 0, 0, 'registered')
                    """,
                    (created_at,)
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not lazily register default workspace: {e}")

    def set_active_workspace(self, project_id: str) -> None:
        """Sets the active workspace. Verifies the workspace exists."""
        project = self.get_workspace(project_id)
        if not project:
            logger.warning(f"Unknown workspace: {project_id}")
            raise ValueError(f"Workspace '{project_id}' is not registered.")
        
        WorkspaceManager._active_project_id = project_id
        logger.info(f"Workspace selected: {project_id}")

    def register_workspace(
        self,
        project_id: str,
        alias: str,
        root_path: str
    ) -> Dict[str, Any]:
        """Registers a new workspace in the master projects registry."""
        if not project_id or not project_id.strip():
            raise ValueError("project_id cannot be empty")
        
        # Format registry values
        project_id = project_id.strip()
        alias = alias.strip()
        root_path = root_path.strip()

        # Check duplicate alias in registry
        existing = self.list_workspaces()
        for p in existing:
            if p["alias"].lower() == alias.lower() and p["project_id"] != project_id:
                logger.warning(f"Duplicate alias: {alias}")
                raise ValueError(f"Workspace alias '{alias}' is already registered.")

        created_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # Write to master registry DB
        from ecip_core.storage.sqlite.database import Database
        conn = Database.get_registry_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO projects (
                    project_id, alias, root_path, indexed_at, indexed_files, total_chunks, total_vectors, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, alias, root_path, created_at, 0, 0, 0, "registered")
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Workspace initialization failed for {project_id}: {e}")
            raise RuntimeError(f"Could not write registry data: {e}")

        # Initialize the project-specific DB schema
        try:
            # Temporarily activate to trigger schema initialization
            old_active = WorkspaceManager._active_project_id
            WorkspaceManager._active_project_id = project_id
            db = Database()
            db.initialize()
            
            # Record project metadata in project-specific DB as well to keep it self-contained
            cursor = db.get_connection().cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO projects (
                    project_id, alias, root_path, indexed_at, indexed_files, total_chunks, total_vectors, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, alias, root_path, created_at, 0, 0, 0, "registered")
            )
            db.get_connection().commit()
            
            WorkspaceManager._active_project_id = old_active
        except Exception as e:
            logger.error(f"Workspace initialization failed for project DB {project_id}: {e}")
            raise

        logger.info(f"Workspace created: {project_id} ({alias})")
        return {
            "project_id": project_id,
            "alias": alias,
            "root_path": root_path,
            "created_at": created_at,
            "status": "registered"
        }

    def get_workspace(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of a registered workspace."""
        self._ensure_default_registered()
        from ecip_core.storage.sqlite.database import Database
        conn = Database.get_registry_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT project_id, alias, root_path, indexed_at, indexed_files, total_chunks, total_vectors, status FROM projects WHERE project_id = ?",
                (project_id,)
            )
            r = cursor.fetchone()
            if r:
                return {
                    "project_id": r[0],
                    "alias": r[1],
                    "root_path": r[2],
                    "indexed_at": r[3],
                    "indexed_files": r[4],
                    "total_chunks": r[5],
                    "total_vectors": r[6],
                    "status": r[7]
                }
            return None
        except Exception:
            return None

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """Lists all registered workspaces from the master registry."""
        self._ensure_default_registered()
        from ecip_core.storage.sqlite.database import Database
        conn = Database.get_registry_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id, alias, root_path, indexed_at, indexed_files, total_chunks, total_vectors, status FROM projects")
            rows = cursor.fetchall()
            return [
                {
                    "project_id": r[0],
                    "alias": r[1],
                    "root_path": r[2],
                    "indexed_at": r[3],
                    "indexed_files": r[4],
                    "total_chunks": r[5],
                    "total_vectors": r[6],
                    "status": r[7]
                }
                for r in rows
            ]
        except Exception:
            return []

    def delete_workspace(self, project_id: str) -> None:
        """Deletes database file, FAISS vector files, and cache entries for project."""
        project = self.get_workspace(project_id)
        if not project:
            logger.warning(f"Unknown workspace: {project_id}")
            return

        from ecip_core.storage.sqlite.database import Database
        # 1. Clear database registry entry
        conn = Database.get_registry_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Cleanup failure in registry DB: {e}")

        # 2. Delete project specific DB file
        if project_id != "default":
            try:
                db_file = Path(f"data/ecip_{project_id}.db")
                if db_file.exists():
                    # Close connection first if active
                    if Database._active_db_path == str(db_file) and Database._connection:
                        Database._connection.close()
                        Database._connection = None
                    db_file.unlink()
            except Exception as e:
                logger.error(f"Cleanup failure deleting SQLite file: {e}")

        # 3. Clean FAISS Index files
        try:
            root_path = project.get("root_path")
            if root_path:
                ecip_dir = Path(root_path) / ".ecip"
                try:
                    shutil.rmtree(ecip_dir)
                except FileNotFoundError:
                    pass
            
            idx_file = Path(f".ecip/faiss_{project_id}.index")
            meta_file = Path(f".ecip/faiss_metadata_{project_id}.json")
            if idx_file.exists():
                idx_file.unlink()
            if meta_file.exists():
                meta_file.unlink()
        except Exception as e:
            logger.error(f"Cleanup failure deleting FAISS index: {e}")

        # 4. Evict cache entries
        try:
            from ecip_core.cache.manager import cache_manager
            # Clear all cache keys starting with project_id namespace
            if cache_manager.disk_store:
                cache_dir = cache_manager.disk_store.cache_dir
                if cache_dir.exists():
                    # We look for pickling cache keys containing project_id or clear memory cache
                    cache_manager.clear()
        except Exception as e:
            logger.error(f"Cleanup failure during cache invalidation: {e}")

        # If deleted active workspace, fall back to default
        if WorkspaceManager._active_project_id == project_id:
            WorkspaceManager._active_project_id = "default"

        logger.info(f"Workspace removed: {project_id}")

    def get_workspace_stats(self, project_id: str) -> Dict[str, Any]:
        """Gathers runtime stats for files, vectors, and dependency edges."""
        project = self.get_workspace(project_id)
        if not project:
            raise ValueError(f"Workspace '{project_id}' is not registered.")

        # Temporarily activate DB connection to extract stats
        old_active = WorkspaceManager._active_project_id
        WorkspaceManager._active_project_id = project_id
        from ecip_core.storage.sqlite.database import Database
        db = Database()
        
        files_count = 0
        chunks_count = 0
        edges_count = 0

        try:
            cursor = db.get_connection().cursor()
            cursor.execute("SELECT COUNT(*) FROM java_files")
            files_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM java_methods")
            chunks_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM dependency_edges")
            edges_count = cursor.fetchone()[0]
        except Exception:
            pass
        finally:
            WorkspaceManager._active_project_id = old_active

        return {
            "project_id": project_id,
            "alias": project["alias"],
            "files_count": files_count,
            "chunks_count": chunks_count,
            "dependency_edges_count": edges_count,
            "status": project["status"]
        }


workspace_manager = WorkspaceManager()

