import os
import tempfile
import unittest
import shutil
from ecip_core.parser.sql.sql_parser import SqlParser


class TestSqlParser(unittest.TestCase):

    def setUp(self):
        self.parser = SqlParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_sql_file(self, filename: str, content: str) -> str:
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_schema_and_flyway_migration_parsing(self):
        sql_content = """
        -- User schema setup
        CREATE TABLE users (
            id INT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100),
            created_at TIMESTAMP
        );

        CREATE TABLE orders (
            order_id INT,
            user_id INT,
            amount DECIMAL(10,2),
            PRIMARY KEY (order_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE UNIQUE INDEX idx_user_email ON users(email);

        CREATE VIEW user_order_summary AS 
        SELECT u.username, COUNT(o.order_id) FROM users u JOIN orders o ON u.id = o.user_id;

        CREATE PROCEDURE get_user_orders() 
        BEGIN
            SELECT 1;
        END;
        """

        filepath = self.write_sql_file("V1__create_tables.sql", sql_content)
        meta = self.parser.parse(filepath)

        # Verify Tables
        self.assertEqual(len(meta.tables), 2)
        table_names = [t.name for t in meta.tables]
        self.assertIn("users", table_names)
        self.assertIn("orders", table_names)

        # Verify Columns
        users_table = next(t for t in meta.tables if t.name == "users")
        self.assertEqual(len(users_table.columns), 4)
        id_col = next(c for c in users_table.columns if c.name == "id")
        self.assertTrue(id_col.is_primary)
        self.assertFalse(id_col.is_nullable)

        # Verify Indexes
        self.assertEqual(len(meta.indexes), 1)
        self.assertEqual(meta.indexes[0].name, "idx_user_email")
        self.assertEqual(meta.indexes[0].table_name, "users")

        # Verify Views and Procedures
        self.assertEqual(len(meta.views), 1)
        self.assertEqual(meta.views[0].name, "user_order_summary")
        self.assertEqual(len(meta.procedures), 1)
        self.assertEqual(meta.procedures[0].name, "get_user_orders")

    def test_empty_sql_file(self):
        filepath = self.write_sql_file("empty.sql", "")
        meta = self.parser.parse(filepath)
        self.assertEqual(len(meta.tables), 0)


if __name__ == "__main__":
    unittest.main()
