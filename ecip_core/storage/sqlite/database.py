import sqlite3
from pathlib import Path


class Database:

    _connection = None

    def __init__(self):

        if Database._connection is None:

            db_dir = Path("data")
            db_dir.mkdir(exist_ok=True)

            Database._connection = sqlite3.connect(
                db_dir / "ecip.db"
            )

            self.connection = Database._connection

            self.initialize()

        else:
            self.connection = Database._connection

    def initialize(self):

        cursor = self.connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS java_files (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_path TEXT UNIQUE,
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

    def get_connection(self):

        return self.connection