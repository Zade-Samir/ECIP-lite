import unittest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

from ecip_core.parser.java.project_parser import JavaProjectParser
from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.scanner.project_scanner import ProjectScanner


class TestJavaProjectParser(unittest.TestCase):

    def setUp(self):
        self.project_parser = JavaProjectParser()

        # Configure logger to capture outputs
        self.log_capture = []

        class CaptureHandler(logging.Handler):
            def __init__(self, capture_list):
                super().__init__()
                self.capture_list = capture_list

            def emit(self, record):
                self.capture_list.append((record.levelname, record.getMessage()))

        from ecip_core.parser.java.project_parser import logger as parser_logger
        self.handler = CaptureHandler(self.log_capture)
        parser_logger.addHandler(self.handler)
        parser_logger.setLevel(logging.DEBUG)

    def tearDown(self):
        from ecip_core.parser.java.project_parser import logger as parser_logger
        parser_logger.removeHandler(self.handler)

    def test_one_parser_call_per_file(self):
        # Scan returns 2 files
        files = [Path("FileA.java"), Path("FileB.java")]
        
        with patch.object(ProjectScanner, 'scan', return_value=files):
            with patch.object(JavaParser, 'parse') as mock_parse:
                mock_parse.return_value = ParsedJavaFile(
                    file_name="File.java", file_path="path", package_name="pkg", class_name="Cls", methods=[]
                )
                self.project_parser.parse_project("dummy_path")
                
                # Assert parse called exactly once for str(FileA.java) and once for str(FileB.java)
                self.assertEqual(mock_parse.call_count, 2)
                mock_parse.assert_any_call("FileA.java")
                mock_parse.assert_any_call("FileB.java")

    def test_one_parsed_java_file_per_source_file(self):
        files = [Path("FileA.java"), Path("FileB.java")]
        
        with patch.object(ProjectScanner, 'scan', return_value=files):
            with patch.object(JavaParser, 'parse') as mock_parse:
                mock_parse.side_effect = [
                    ParsedJavaFile(file_name="FileA.java", file_path="A", package_name="pkg", class_name="A", methods=[]),
                    ParsedJavaFile(file_name="FileB.java", file_path="B", package_name="pkg", class_name="B", methods=[])
                ]
                results = self.project_parser.parse_project("dummy_path")
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0].file_name, "FileA.java")
                self.assertEqual(results[1].file_name, "FileB.java")

    def test_correct_file_count(self):
        # Empty project
        with patch.object(ProjectScanner, 'scan', return_value=[]):
            results = self.project_parser.parse_project("dummy_path")
            self.assertEqual(len(results), 0)
            
            log_msgs = [msg for level, msg in self.log_capture]
            self.assertIn("Project parsing started", log_msgs)
            self.assertIn("Parsing completed", log_msgs)
            self.assertIn("Total parsed files: 0", log_msgs)

    def test_unsupported_files_ignored(self):
        files = [Path("FileA.java"), Path("Readme.txt"), Path("Script.py")]
        
        with patch.object(ProjectScanner, 'scan', return_value=files):
            with patch.object(JavaParser, 'parse') as mock_parse:
                mock_parse.return_value = ParsedJavaFile(
                    file_name="FileA.java", file_path="A", package_name="pkg", class_name="A", methods=[]
                )
                results = self.project_parser.parse_project("dummy_path")
                
                # Should only parse FileA.java
                self.assertEqual(len(results), 1)
                mock_parse.assert_called_once_with("FileA.java")
                
                # Verify warning log for ignored files
                log_levels = [level for level, msg in self.log_capture]
                log_msgs = [msg for level, msg in self.log_capture]
                self.assertIn("WARNING", log_levels)
                self.assertTrue(any("Unsupported file skipped" in msg for msg in log_msgs))

    def test_parser_exception_handling(self):
        files = [Path("FileA.java"), Path("FileB.java")]
        
        with patch.object(ProjectScanner, 'scan', return_value=files):
            with patch.object(JavaParser, 'parse') as mock_parse:
                # First parse fails with exception, second succeeds
                mock_parse.side_effect = [
                    ValueError("Syntax error in FileA"),
                    ParsedJavaFile(file_name="FileB.java", file_path="B", package_name="pkg", class_name="B", methods=[])
                ]
                
                results = self.project_parser.parse_project("dummy_path")
                
                # Should continue parsing and return FileB.java
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].file_name, "FileB.java")
                
                # Verify error log
                log_levels = [level for level, msg in self.log_capture]
                log_msgs = [msg for level, msg in self.log_capture]
                self.assertIn("ERROR", log_levels)
                self.assertIn("Parser failure", log_msgs)
                self.assertTrue(any("File path: FileA.java" in msg for msg in log_msgs))
                self.assertTrue(any("Exception message: Syntax error in FileA" in msg for msg in log_msgs))

    def test_integration_against_sample_project(self):
        sample_path = "projects/sampleProject"
        results = self.project_parser.parse_project(sample_path)
        
        # Verify 3 files are parsed: UserController, UserRepository, UserService
        self.assertEqual(len(results), 3)
        
        # Verify paths are unique (no duplicates due to repeated parsing)
        paths = [r.file_path for r in results]
        self.assertEqual(len(paths), len(set(paths)))
        
        # Verify class names are unique
        classes = [r.class_name for r in results]
        self.assertEqual(len(classes), len(set(classes)))
        
        # Confirm deterministic sorted ordering (UserController, UserRepository, UserService)
        self.assertEqual(results[0].file_name, "UserController.java")
        self.assertEqual(results[1].file_name, "UserRepository.java")
        self.assertEqual(results[2].file_name, "UserService.java")


if __name__ == "__main__":
    unittest.main()
