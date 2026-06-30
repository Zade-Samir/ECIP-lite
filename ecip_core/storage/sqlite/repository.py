from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.storage.sqlite.database import Database


class JavaRepository:

    def __init__(self):

        self.connection = Database().get_connection()

    def save(
        self,
        parsed_file: ParsedJavaFile
    ):

        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO java_files
            (
                file_name,
                file_path,
                package_name,
                class_name
            )
            VALUES
            (?, ?, ?, ?)
            """,
            (
                parsed_file.file_name,
                parsed_file.file_path,
                parsed_file.package_name,
                parsed_file.class_name,
            ),
        )

        file_id = cursor.lastrowid

        for method in parsed_file.methods:

            cursor.execute(
                """
                INSERT INTO java_methods
                (
                    file_id,
                    method_name
                )
                VALUES
                (?, ?)
                """,
                (
                    file_id,
                    method,
                ),
            )

        self.connection.commit()