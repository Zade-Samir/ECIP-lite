import sqlite3
from pathlib import Path


class Database:

    def __init__(self):

        db_dir = Path("data")

        db_dir.mkdir(exist_ok=True)

        self.connection = sqlite3.connect(
            db_dir / "ecip.db"
        )

    def get_connection(self):

        return self.connection