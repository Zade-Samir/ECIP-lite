from ecip_core.storage.sqlite.database import Database


class SchemaManager:

    def __init__(self):

        self.connection = Database().get_connection()

    def create_tables(self):

        cursor = self.connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS java_files (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_path TEXT,
            package_name TEXT,
            class_name TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS java_methods (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            method_name TEXT,
            FOREIGN KEY(file_id)
            REFERENCES java_files(id)
        );
        """)

        self.connection.commit()