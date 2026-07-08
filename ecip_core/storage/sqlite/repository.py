from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.storage.sqlite.database import Database
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class JavaRepository:

    def __init__(self):

        self.connection = Database().get_connection()

    def save(self, parsed_file: ParsedJavaFile, file_hash: str = ""):

        logger.info("Database opened")
        logger.info("Saving metadata")

        try:
            cursor = self.connection.cursor()

            # Step 1
            cursor.execute(
                """
                SELECT id
                FROM java_files
                WHERE file_path = ?
                """,
                (parsed_file.file_path,)
            )

            existing = cursor.fetchone()

            if existing:

                file_id = existing[0]
                logger.warning("Duplicate metadata")

                # Update metadata including file_hash
                cursor.execute(
                    """
                    UPDATE java_files
                    SET
                        file_name = ?,
                        package_name = ?,
                        class_name = ?,
                        file_hash = ?
                    WHERE id = ?
                    """,
                    (
                        parsed_file.file_name,
                        parsed_file.package_name,
                        parsed_file.class_name,
                        file_hash,
                        file_id,
                    ),
                )

                # Remove old methods
                cursor.execute(
                    """
                    DELETE FROM java_methods
                    WHERE file_id = ?
                    """,
                    (file_id,),
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO java_files
                    (
                        file_name,
                        file_path,
                        package_name,
                        class_name,
                        file_hash
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        parsed_file.file_name,
                        parsed_file.file_path,
                        parsed_file.package_name,
                        parsed_file.class_name,
                        file_hash,
                    ),
                )

                file_id = cursor.lastrowid

            # Insert fresh methods
            for method in parsed_file.methods:

                cursor.execute(
                    """
                    INSERT INTO java_methods
                    (
                        file_id,
                        method_name
                    )
                    VALUES (?, ?)
                    """,
                    (
                        file_id,
                        method.name,
                    ),
                )

            self.connection.commit()
            logger.info("Commit successful")

        except Exception as e:
            logger.error("Database failure")
            logger.error("Insert failed")
            try:
                self.connection.rollback()
                logger.error("Rollback executed")
            except Exception as rollback_err:
                logger.error(f"Rollback failed: {rollback_err}")
            raise e

    def get_file_hash(self, file_path: str) -> str | None:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT file_hash
                FROM java_files
                WHERE file_path = ?
                """,
                (file_path,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error("Database failure")
            raise e

    def get_all_file_paths(self) -> list[str]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT file_path FROM java_files")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error("Database failure")
            raise e

    def delete_by_file_path(self, file_path: str):
        logger.info("File removed")
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id
                FROM java_files
                WHERE file_path = ?
                """,
                (file_path,)
            )
            row = cursor.fetchone()
            if row:
                file_id = row[0]
                cursor.execute(
                    """
                    DELETE FROM java_methods
                    WHERE file_id = ?
                    """,
                    (file_id,)
                )
                cursor.execute(
                    """
                    DELETE FROM java_files
                    WHERE id = ?
                    """,
                    (file_id,)
                )
                self.connection.commit()
        except Exception as e:
            logger.error("Database failure")
            try:
                self.connection.rollback()
            except Exception:
                pass
            raise e

    def get_all_files(self) -> list[dict]:

        logger.info("Fetching all Java files")

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                file_name,
                package_name,
                class_name
            FROM java_files
        """)

        rows = cursor.fetchall()

        return [
            {
                "file_name": row[0],
                "package_name": row[1],
                "class_name": row[2]
            }
            for row in rows
        ]

    def find_by_class_name(
            self,
            class_name: str
        ) -> dict | None:

        logger.info(f"Searching class: {class_name}")

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                *
            FROM java_files
            WHERE class_name = ?
            """,
            (class_name,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "file_name": row[1],
            "file_path": row[2],
            "package_name": row[3],
            "class_name": row[4],
        }

    def find_methods(
            self,
            class_name: str
        ) -> list[str]:

        logger.info(f"Fetching methods of class: {class_name}")

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                jm.method_name
            FROM java_methods jm
            JOIN java_files jf
                ON jm.file_id = jf.id
            WHERE jf.class_name = ?
            """,
            (class_name,)
        )

        rows = cursor.fetchall()

        return [
            row[0]
            for row in rows
        ]

    def find_file_by_method(
            self,
            method_name: str
        ):

        logger.info(f"Searching method: {method_name}")

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                jf.file_name,
                jf.class_name
            FROM java_files jf
            JOIN java_methods jm
                ON jf.id = jm.file_id
            WHERE jm.method_name = ?
            """,
            (method_name,)
        )

        rows = cursor.fetchall()

        return [
            row[0]
            for row in rows
        ]

    def search_classes(self, query: str, exact: bool = True) -> list[dict]:
        try:
            cursor = self.connection.cursor()
            if exact:
                cursor.execute(
                    "SELECT id, file_name, file_path, package_name, class_name FROM java_files WHERE class_name = ?",
                    (query,)
                )
            else:
                cursor.execute(
                    "SELECT id, file_name, file_path, package_name, class_name FROM java_files WHERE class_name LIKE ?",
                    (f"{query}%",)
                )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "file_name": r[1],
                    "file_path": r[2],
                    "package_name": r[3],
                    "class_name": r[4],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Database failure")
            raise e

    def search_methods(self, query: str, exact: bool = True) -> list[dict]:
        try:
            cursor = self.connection.cursor()
            if exact:
                cursor.execute(
                    """
                    SELECT jf.id, jf.file_name, jf.file_path, jf.package_name, jf.class_name, jm.method_name
                    FROM java_methods jm
                    JOIN java_files jf ON jm.file_id = jf.id
                    WHERE jm.method_name = ?
                    """,
                    (query,)
                )
            else:
                cursor.execute(
                    """
                    SELECT jf.id, jf.file_name, jf.file_path, jf.package_name, jf.class_name, jm.method_name
                    FROM java_methods jm
                    JOIN java_files jf ON jm.file_id = jf.id
                    WHERE jm.method_name LIKE ?
                    """,
                    (f"{query}%",)
                )
            rows = cursor.fetchall()
            return [
                {
                    "file_id": r[0],
                    "file_name": r[1],
                    "file_path": r[2],
                    "package_name": r[3],
                    "class_name": r[4],
                    "method_name": r[5],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Database failure")
            raise e

    def search_packages(self, query: str, exact: bool = True) -> list[dict]:
        try:
            cursor = self.connection.cursor()
            if exact:
                cursor.execute(
                    "SELECT id, file_name, file_path, package_name, class_name FROM java_files WHERE package_name = ?",
                    (query,)
                )
            else:
                cursor.execute(
                    "SELECT id, file_name, file_path, package_name, class_name FROM java_files WHERE package_name LIKE ?",
                    (f"{query}%",)
                )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "file_name": r[1],
                    "file_path": r[2],
                    "package_name": r[3],
                    "class_name": r[4],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Database failure")
            raise e

    def search_file_paths(self, query: str, exact: bool = True) -> list[dict]:
        try:
            cursor = self.connection.cursor()
            if exact:
                cursor.execute(
                    "SELECT id, file_name, file_path, package_name, class_name FROM java_files WHERE file_path = ?",
                    (query,)
                )
            else:
                cursor.execute(
                    "SELECT id, file_name, file_path, package_name, class_name FROM java_files WHERE file_path LIKE ?",
                    (f"{query}%",)
                )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "file_name": r[1],
                    "file_path": r[2],
                    "package_name": r[3],
                    "class_name": r[4],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Database failure")
            raise e

    def save_project(
        self,
        project_id: str,
        alias: str,
        root_path: str,
        indexed_at: str,
        indexed_files: int,
        total_chunks: int,
        total_vectors: int,
        status: str
    ):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO projects (
                    project_id, alias, root_path, indexed_at, indexed_files, total_chunks, total_vectors, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, alias, root_path, indexed_at, indexed_files, total_chunks, total_vectors, status)
            )
            self.connection.commit()
        except Exception as e:
            logger.error("Database failure")
            raise e

    def get_projects(self) -> list[dict]:
        try:
            cursor = self.connection.cursor()
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
        except Exception as e:
            logger.error("Database failure")
            raise e

    def get_project(self, project_id: str) -> dict | None:
        try:
            cursor = self.connection.cursor()
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
        except Exception as e:
            logger.error("Database failure")
            raise e

    def delete_project(self, project_id: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT root_path FROM projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                root_path = row[0]
                
                cursor.execute("SELECT id FROM java_files WHERE file_path LIKE ?", (root_path + "%",))
                file_ids = [r[0] for r in cursor.fetchall()]
                
                if file_ids:
                    placeholders = ",".join("?" for _ in file_ids)
                    cursor.execute(f"DELETE FROM java_methods WHERE file_id IN ({placeholders})", tuple(file_ids))
                    cursor.execute("DELETE FROM java_files WHERE file_path LIKE ?", (root_path + "%",))
                
                cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM dependency_edges WHERE project_id = ?", (project_id,))
                self.connection.commit()
        except Exception as e:
            logger.error("Database failure")
            raise e

    def delete_class_edges(self, project_id: str, class_name: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM dependency_edges WHERE project_id = ? AND source_class = ?",
                (project_id, class_name)
            )
            self.connection.commit()
        except Exception as e:
            logger.error("Database failure")
            raise e

    def save_edge(
        self,
        project_id: str,
        source_class: str,
        target_class: str,
        relationship_type: str
    ) -> bool:
        import datetime
        try:
            cursor = self.connection.cursor()
            
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
            self.connection.commit()
            return True
        except Exception as e:
            logger.error("Database failure")
            raise e

    def get_edges(self, project_id: str) -> list[dict]:
        try:
            cursor = self.connection.cursor()
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
            logger.error("Database failure")
            raise e

    def get_graph_stats(self, project_id: str) -> dict:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM dependency_edges WHERE project_id = ?",
                (project_id,)
            )
            total_edges = cursor.fetchone()[0]
            return {"total_edges": total_edges}
        except Exception as e:
            logger.error("Database failure")
            raise e

    def get_outgoing_edges(self, project_id: str, class_name: str) -> list[dict]:
        try:
            cursor = self.connection.cursor()
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
            logger.error("Database failure")
            raise e

    def get_incoming_edges(self, project_id: str, class_name: str) -> list[dict]:
        try:
            cursor = self.connection.cursor()
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
            logger.error("Database failure")
            raise e

    def get_all_class_edges(self, project_id: str, class_name: str) -> list[dict]:
        try:
            cursor = self.connection.cursor()
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
            logger.error("Database failure")
            raise e