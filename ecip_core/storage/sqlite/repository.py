from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.storage.sqlite.database import Database
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)

class JavaRepository:

    def __init__(self):

        self.connection = Database().get_connection()

    def save(self, parsed_file: ParsedJavaFile):

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

                # Update metadata
                cursor.execute(
                    """
                    UPDATE java_files
                    SET
                        file_name = ?,
                        package_name = ?,
                        class_name = ?
                    WHERE id = ?
                    """,
                    (
                        parsed_file.file_name,
                        parsed_file.package_name,
                        parsed_file.class_name,
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
                        class_name
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        parsed_file.file_name,
                        parsed_file.file_path,
                        parsed_file.package_name,
                        parsed_file.class_name,
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
            logger.error("Insert failed")
            try:
                self.connection.rollback()
                logger.error("Rollback executed")
            except Exception as rollback_err:
                logger.error(f"Rollback failed: {rollback_err}")
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