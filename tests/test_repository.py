import unittest
import sqlite3
import logging
from unittest.mock import patch

from ecip_core.storage.sqlite.database import Database
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.parser.models.method_info import MethodInfo
from ecip_core.parser.java.java_parser import JavaParser


class TestJavaRepository(unittest.TestCase):

    def setUp(self):
        # Reset database connection to in-memory database for isolation
        Database._connection = sqlite3.connect(":memory:")
        self.db = Database()
        self.db.initialize()
        self.repo = JavaRepository()
        self.repo.connection = Database._connection

        # Configure logger to capture outputs
        self.log_capture = []

        class CaptureHandler(logging.Handler):
            def __init__(self, capture_list):
                super().__init__()
                self.capture_list = capture_list

            def emit(self, record):
                self.capture_list.append((record.levelname, record.getMessage()))

        from ecip_core.storage.sqlite.repository import logger as repo_logger
        self.handler = CaptureHandler(self.log_capture)
        repo_logger.addHandler(self.handler)
        repo_logger.setLevel(logging.DEBUG)

    def tearDown(self):
        from ecip_core.storage.sqlite.repository import logger as repo_logger
        repo_logger.removeHandler(self.handler)
        Database._connection.close()
        Database._connection = None

    def test_successful_insert(self):
        methods = [
            MethodInfo(name="calculateSum", start_line=10, end_line=15),
            MethodInfo(name="printResult", start_line=18, end_line=20)
        ]
        parsed_file = ParsedJavaFile(
            file_name="Calculator.java",
            file_path="/src/main/java/com/example/Calculator.java",
            package_name="com.example",
            class_name="Calculator",
            methods=methods
        )

        self.repo.save(parsed_file)

        # Check logs
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Database opened", log_msgs)
        self.assertIn("Saving metadata", log_msgs)
        self.assertIn("Commit successful", log_msgs)

        # Query database to check values
        cursor = self.repo.connection.cursor()
        cursor.execute("SELECT * FROM java_files")
        files = cursor.fetchall()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0][1], "Calculator.java")
        self.assertEqual(files[0][2], "/src/main/java/com/example/Calculator.java")
        self.assertEqual(files[0][3], "com.example")
        self.assertEqual(files[0][4], "Calculator")

        cursor.execute("SELECT * FROM java_methods")
        db_methods = cursor.fetchall()
        self.assertEqual(len(db_methods), 2)
        self.assertEqual(db_methods[0][1], files[0][0])
        self.assertEqual(db_methods[0][2], "calculateSum")
        self.assertEqual(db_methods[1][1], files[0][0])
        self.assertEqual(db_methods[1][2], "printResult")

    def test_duplicate_handling(self):
        methods1 = [
            MethodInfo(name="calculateSum", start_line=10, end_line=15)
        ]
        parsed_file = ParsedJavaFile(
            file_name="Calculator.java",
            file_path="/src/main/java/com/example/Calculator.java",
            package_name="com.example",
            class_name="Calculator",
            methods=methods1
        )
        self.repo.save(parsed_file)
        self.log_capture.clear()

        # Update metadata of duplicate file path (with different class & methods)
        methods2 = [
            MethodInfo(name="printResult", start_line=18, end_line=20)
        ]
        updated_file = ParsedJavaFile(
            file_name="Calculator.java",
            file_path="/src/main/java/com/example/Calculator.java",
            package_name="com.example",
            class_name="NewCalculator",
            methods=methods2
        )
        self.repo.save(updated_file)

        # Check duplicate metadata warning logged
        log_levels = [level for level, msg in self.log_capture]
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("WARNING", log_levels)
        self.assertIn("Duplicate metadata", log_msgs)

        # Verify database is updated and old methods removed
        cursor = self.repo.connection.cursor()
        cursor.execute("SELECT * FROM java_files")
        files = cursor.fetchall()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0][4], "NewCalculator")

        cursor.execute("SELECT * FROM java_methods")
        db_methods = cursor.fetchall()
        self.assertEqual(len(db_methods), 1)
        self.assertEqual(db_methods[0][2], "printResult")

    def test_rollback_on_failure(self):
        parsed_file = ParsedJavaFile(
            file_name="ErrorFile.java",
            file_path="/src/ErrorFile.java",
            package_name="error",
            class_name="ErrorFile",
            methods=[MethodInfo(name="someMethod", start_line=1, end_line=2)]
        )

        class FaultyCursor:
            def __init__(self, real):
                self.real = real

            def execute(self, sql, params=()):
                if "INSERT INTO java_methods" in sql:
                    raise sqlite3.IntegrityError("Simulated write failure")
                return self.real.execute(sql, params)

            def fetchone(self):
                return self.real.fetchone()

            @property
            def lastrowid(self):
                return self.real.lastrowid

        class FaultyConnection:
            def __init__(self, real):
                self.real = real

            def cursor(self):
                return FaultyCursor(self.real.cursor())

            def commit(self):
                self.real.commit()

            def rollback(self):
                self.real.rollback()

        original_connection = self.repo.connection
        self.repo.connection = FaultyConnection(original_connection)

        try:
            with self.assertRaises(sqlite3.IntegrityError):
                self.repo.save(parsed_file)
        finally:
            self.repo.connection = original_connection

        # Check rollback and insert failed logging
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Insert failed", log_msgs)
        self.assertIn("Rollback executed", log_msgs)

        # Verify nothing was persisted (java_files should be empty because of rollback)
        cursor = self.repo.connection.cursor()
        cursor.execute("SELECT * FROM java_files")
        self.assertEqual(len(cursor.fetchall()), 0)

    def test_unicode_support(self):
        parsed_file = ParsedJavaFile(
            file_name="ČeskýSoubor.java",
            file_path="/src/ČeskýSoubor.java",
            package_name="čeština.balíček",
            class_name="ČeskýSoubor",
            methods=[MethodInfo(name="českáMetoda", start_line=10, end_line=20)]
        )
        self.repo.save(parsed_file)

        cursor = self.repo.connection.cursor()
        cursor.execute("SELECT * FROM java_files")
        files = cursor.fetchall()
        self.assertEqual(files[0][1], "ČeskýSoubor.java")
        self.assertEqual(files[0][2], "/src/ČeskýSoubor.java")
        self.assertEqual(files[0][3], "čeština.balíček")
        self.assertEqual(files[0][4], "ČeskýSoubor")

        cursor.execute("SELECT * FROM java_methods")
        db_methods = cursor.fetchall()
        self.assertEqual(db_methods[0][2], "českáMetoda")

    def test_long_source_code_and_large_input(self):
        long_class_name = "A" * 1000
        long_method_name = "B" * 1000
        parsed_file = ParsedJavaFile(
            file_name="Calculator.java",
            file_path="/src/Calculator.java",
            package_name="com.example",
            class_name=long_class_name,
            methods=[MethodInfo(name=long_method_name, start_line=1, end_line=10000)]
        )
        self.repo.save(parsed_file)

        cursor = self.repo.connection.cursor()
        cursor.execute("SELECT class_name FROM java_files")
        res_class = cursor.fetchone()[0]
        self.assertEqual(res_class, long_class_name)

        cursor.execute("SELECT method_name FROM java_methods")
        res_method = cursor.fetchone()[0]
        self.assertEqual(res_method, long_method_name)

    def test_integration_parser_to_repository(self):
        parser = JavaParser()
        parsed = parser.parse("projects/sampleProject/UserService.java")

        # Save to database
        self.repo.save(parsed)

        # Fetch and verify database content exactly matches parser output
        cursor = self.repo.connection.cursor()
        cursor.execute("SELECT * FROM java_files WHERE file_path = ?", (parsed.file_path,))
        file_row = cursor.fetchone()
        self.assertIsNotNone(file_row)
        self.assertEqual(file_row[1], parsed.file_name)
        self.assertEqual(file_row[3], parsed.package_name)
        self.assertEqual(file_row[4], parsed.class_name)

        cursor.execute("SELECT method_name FROM java_methods WHERE file_id = ?", (file_row[0],))
        db_methods = [row[0] for row in cursor.fetchall()]
        parser_methods = [m.name for m in parsed.methods]
        self.assertEqual(db_methods, parser_methods)


if __name__ == "__main__":
    unittest.main()
