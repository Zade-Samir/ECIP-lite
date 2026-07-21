import sqlite3
import contextvars
from pathlib import Path

_db_connection_var = contextvars.ContextVar("db_connection", default=None)
_db_active_path_var = contextvars.ContextVar("db_active_path", default=None)
_registry_connection_var = contextvars.ContextVar("registry_connection", default=None)


class Database:

    _connection = None
    _active_db_path = None
    _registry_connection = None

    def __init__(self):
        from ecip_core.workspace.manager import WorkspaceManager
        current_db_path = WorkspaceManager.get_active_db_path()

        active_db_path = Database._active_db_path if Database._active_db_path is not None else _db_active_path_var.get()
        connection = Database._connection if Database._connection is not None else _db_connection_var.get()

        if connection is not None:
            try:
                connection.execute("SELECT 1")
            except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
                if "closed" in str(e).lower() or "cannot operate" in str(e).lower():
                    connection = None
                    _db_connection_var.set(None)
                    Database._connection = None

        if active_db_path != current_db_path and Database._active_db_path is None:
            # Cleanly close old connection if it changes
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
                connection = None
                _db_connection_var.set(None)
                Database._connection = None
            _db_active_path_var.set(current_db_path)
            active_db_path = current_db_path

        if connection is None:
            db_file = Path(active_db_path)
            db_file.parent.mkdir(exist_ok=True)
            connection = sqlite3.connect(db_file)
            
            if Database._active_db_path is not None:
                Database._connection = connection
            else:
                _db_connection_var.set(connection)
                
            self.connection = connection
            self.initialize()
        else:
            self.connection = connection

    @classmethod
    def get_registry_connection(cls):
        """Always returns the connection to the master projects registry (data/ecip.db)."""
        reg_conn = cls._registry_connection if cls._registry_connection is not None else _registry_connection_var.get()
        if reg_conn is not None:
            try:
                reg_conn.execute("SELECT 1")
            except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
                if "closed" in str(e).lower() or "cannot operate" in str(e).lower():
                    reg_conn = None
                    _registry_connection_var.set(None)
                    cls._registry_connection = None

        if reg_conn is None:
            db_dir = Path("data")
            db_dir.mkdir(exist_ok=True)
            reg_conn = sqlite3.connect(db_dir / "ecip.db")
            
            if cls._registry_connection is not None or _registry_connection_var.get() is None:
                cls._registry_connection = reg_conn
                _registry_connection_var.set(reg_conn)
            
            db = Database()
            old_active = _db_active_path_var.get()
            
            # Temporarily point connection to registry to run init
            _db_active_path_var.set(str(db_dir / "ecip.db"))
            conn_backup = _db_connection_var.get()
            _db_connection_var.set(reg_conn)
            db.initialize()
            
            # Revert states
            _db_active_path_var.set(old_active)
            _db_connection_var.set(conn_backup)
        return reg_conn

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