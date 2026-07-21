import sqlite3
import datetime
from typing import List, Dict, Any, Optional

from ecip_core.graph.provider import GraphProvider
from ecip_core.storage.sqlite.database import Database
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class SqliteGraphProvider(GraphProvider):
    """
    SQLite implementation of GraphProvider for full backward compatibility.
    """

    def __init__(self):
        self.db = None

    def connect(self) -> None:
        self.db = Database()

    def close(self) -> None:
        self.db = None

    def _get_conn(self):
        if self.db is None:
            self.connect()
        return self.db.get_connection()

    def create_node(self, label: str, properties: Dict[str, Any]) -> None:
        # SQLite nodes are stored implicitly via files/methods/projects tables.
        # This is a no-op as SQLite's relational schema handles node storage in separate tables.
        pass

    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        # Map project_id from properties
        project_id = (properties or {}).get("project_id", "default")
        self.save_edge(project_id, source_id, target_id, rel_type)

    def batch_insert_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        pass

    def batch_insert_relationships(self, relationships: List[Dict[str, Any]]) -> None:
        for rel in relationships:
            src = rel.get("source_id")
            tgt = rel.get("target_id")
            rtype = rel.get("type")
            props = rel.get("properties") or {}
            self.create_relationship(src, tgt, rtype, props)

    def query(self, query_str: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(query_str, parameters or {})
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, r)) for r in rows]

    def save_edge(
        self,
        project_id: str,
        source_class: str,
        target_class: str,
        relationship_type: str
    ) -> bool:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Check for duplicate
            cursor.execute(
                """
                SELECT id FROM dependency_edges
                WHERE project_id = ? AND source_class = ? AND target_class = ? AND relationship_type = ?
                """,
                (project_id, source_class, target_class, relationship_type)
            )
            if cursor.fetchone():
                return False

            discovered_at = datetime.datetime.utcnow().isoformat() + "Z"
            cursor.execute(
                """
                INSERT INTO dependency_edges (
                    project_id, source_class, target_class, relationship_type, discovered_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, source_class, target_class, relationship_type, discovered_at)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e

    def get_edges(self, project_id: str) -> List[Dict[str, Any]]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT source_class, target_class, relationship_type, discovered_at
                FROM dependency_edges WHERE project_id = ?
                """,
                (project_id,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "source_class": r[0],
                    "target_class": r[1],
                    "relationship_type": r[2],
                    "discovered_at": r[3]
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e

    def get_outgoing_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT source_class, target_class, relationship_type, discovered_at
                FROM dependency_edges WHERE project_id = ? AND source_class = ?
                """,
                (project_id, class_name)
            )
            rows = cursor.fetchall()
            return [
                {
                    "source_class": r[0],
                    "target_class": r[1],
                    "relationship_type": r[2],
                    "discovered_at": r[3]
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e

    def get_incoming_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT source_class, target_class, relationship_type, discovered_at
                FROM dependency_edges WHERE project_id = ? AND target_class = ?
                """,
                (project_id, class_name)
            )
            rows = cursor.fetchall()
            return [
                {
                    "source_class": r[0],
                    "target_class": r[1],
                    "relationship_type": r[2],
                    "discovered_at": r[3]
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e

    def get_all_class_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT source_class, target_class, relationship_type, discovered_at
                FROM dependency_edges WHERE project_id = ? AND (source_class = ? OR target_class = ?)
                """,
                (project_id, class_name, class_name)
            )
            rows = cursor.fetchall()
            return [
                {
                    "source_class": r[0],
                    "target_class": r[1],
                    "relationship_type": r[2],
                    "discovered_at": r[3]
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e

    def get_graph_stats(self, project_id: str) -> Dict[str, Any]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM dependency_edges WHERE project_id = ?",
                (project_id,)
            )
            total_edges = cursor.fetchone()[0]
            return {"total_edges": total_edges}
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e

    def delete_class_edges(self, project_id: str, class_name: str) -> None:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM dependency_edges WHERE project_id = ? AND source_class = ?",
                (project_id, class_name)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e

    def delete_project(self, project_id: str) -> None:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dependency_edges WHERE project_id = ?", (project_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"SQLite graph error: {e}")
            raise e
