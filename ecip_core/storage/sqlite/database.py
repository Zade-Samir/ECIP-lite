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
            class_name TEXT,
            file_hash TEXT
        );
        """)

        # Dynamically add file_hash column to existing tables for migration compatibility
        try:
            cursor.execute("ALTER TABLE java_files ADD COLUMN file_hash TEXT;")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS java_methods (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            method_name TEXT,
            FOREIGN KEY(file_id)
            REFERENCES java_files(id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            alias TEXT,
            root_path TEXT UNIQUE,
            indexed_at TEXT,
            indexed_files INTEGER,
            total_chunks INTEGER,
            total_vectors INTEGER,
            status TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dependency_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            source_class TEXT,
            target_class TEXT,
            relationship_type TEXT,
            discovered_at TEXT,
            UNIQUE(project_id, source_class, target_class, relationship_type)
        );
        """)

        self.connection.commit()

    def get_connection(self):

        return self.connection