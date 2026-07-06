import unittest
import logging
import tempfile
import shutil
import javalang
from pathlib import Path

from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile


class TestJavaParserAST(unittest.TestCase):

    def setUp(self):
        self.parser = JavaParser()
        self.temp_dir = tempfile.mkdtemp()
        
        # Configure logger to capture outputs
        self.log_capture = []

        class CaptureHandler(logging.Handler):
            def __init__(self, capture_list):
                super().__init__()
                self.capture_list = capture_list

            def emit(self, record):
                self.capture_list.append((record.levelname, record.getMessage()))

        from ecip_core.parser.java.java_parser import logger as parser_logger
        self.handler = CaptureHandler(self.log_capture)
        parser_logger.addHandler(self.handler)
        parser_logger.setLevel(logging.DEBUG)

    def tearDown(self):
        from ecip_core.parser.java.java_parser import logger as parser_logger
        parser_logger.removeHandler(self.handler)
        shutil.rmtree(self.temp_dir)

    def write_temp_file(self, content: str, filename: str = "TestClass.java") -> str:
        filepath = Path(self.temp_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)

    def test_rest_controller_parsing(self):
        content = """
        package com.example.controller;
        
        import org.springframework.web.bind.annotation.*;
        
        @RestController
        @RequestMapping("/api")
        public class MyController {
            
            private final MyService service;
            
            public MyController(MyService service) {
                this.service = service;
            }
            
            @GetMapping("/data")
            public List<String> getData(@RequestParam String query) {
                return service.fetch(query);
            }
        }
        """
        filepath = self.write_temp_file(content, "MyController.java")
        parsed = self.parser.parse(filepath)
        
        # Assert class structure
        self.assertEqual(parsed.class_name, "MyController")
        self.assertIn("@RestController", parsed.class_annotations)
        self.assertIn("@RequestMapping", parsed.class_annotations)
        self.assertEqual(parsed.package_name, "com.example.controller")
        self.assertEqual(parsed.imports, ["org.springframework.web.bind.annotation.*"])
        self.assertEqual(parsed.constructors, ["MyController"])
        self.assertEqual(parsed.fields, ["private final MyService service"])
        self.assertEqual(parsed.source_code, content)
        
        # Assert method structure
        self.assertEqual(len(parsed.methods), 1)
        method = parsed.methods[0]
        self.assertEqual(method.name, "getData")
        self.assertEqual(method.return_type, "List<String>")
        self.assertIn("@GetMapping", method.annotations)
        self.assertEqual(method.parameters, ["String query"])
        self.assertEqual(method.modifiers, ["public"])
        self.assertEqual(method.signature, "public List<String> getData(String query)")
        
        # Assert line numbers (1-based index)
        # MyController start line: ~7. getData start line: ~15.
        self.assertGreater(method.start_line, 10)
        self.assertGreater(method.end_line, method.start_line)

        # Assert correct logs
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Parsing started", log_msgs)
        self.assertIn("AST created", log_msgs)
        self.assertIn("Class discovered", log_msgs)
        self.assertIn("Methods extracted", log_msgs)
        self.assertIn("Parsing completed", log_msgs)

    def test_service_parsing(self):
        content = """
        package com.example.service;
        
        import org.springframework.stereotype.Service;
        
        @Service
        public class MyService {
            public void execute() {
                // do nothing
            }
        }
        """
        filepath = self.write_temp_file(content, "MyService.java")
        parsed = self.parser.parse(filepath)
        
        self.assertEqual(parsed.class_name, "MyService")
        self.assertIn("@Service", parsed.class_annotations)
        self.assertEqual(len(parsed.methods), 1)
        self.assertEqual(parsed.methods[0].name, "execute")

    def test_repository_parsing(self):
        content = """
        package com.example.repository;
        
        import org.springframework.stereotype.Repository;
        
        @Repository
        public class MyRepository {
            public int count() {
                return 0;
            }
        }
        """
        filepath = self.write_temp_file(content, "MyRepository.java")
        parsed = self.parser.parse(filepath)
        
        self.assertEqual(parsed.class_name, "MyRepository")
        self.assertIn("@Repository", parsed.class_annotations)

    def test_entity_parsing(self):
        content = """
        package com.example.model;
        
        import javax.persistence.Entity;
        
        @Entity
        public class User {
            private Long id;
        }
        """
        filepath = self.write_temp_file(content, "User.java")
        parsed = self.parser.parse(filepath)
        
        self.assertEqual(parsed.class_name, "User")
        self.assertIn("@Entity", parsed.class_annotations)
        self.assertEqual(parsed.fields, ["private Long id"])

    def test_interface_parsing(self):
        content = """
        package com.example.repository;
        
        public interface BaseInterface extends Comparable<BaseInterface> {
            void performAction(int count);
        }
        """
        filepath = self.write_temp_file(content, "BaseInterface.java")
        parsed = self.parser.parse(filepath)
        
        self.assertEqual(parsed.class_name, "BaseInterface")
        self.assertIn("Comparable", parsed.interfaces)
        self.assertEqual(len(parsed.methods), 1)
        
        method = parsed.methods[0]
        self.assertEqual(method.name, "performAction")
        self.assertEqual(method.return_type, "void")
        self.assertEqual(method.parameters, ["int count"])
        # Interface method without body
        self.assertEqual(method.start_line, method.end_line)

    def test_enum_parsing(self):
        content = """
        package com.example.model;
        
        public enum Status {
            ACTIVE, INACTIVE;
            
            public boolean isActive() {
                return this == ACTIVE;
            }
        }
        """
        filepath = self.write_temp_file(content, "Status.java")
        parsed = self.parser.parse(filepath)
        
        self.assertEqual(parsed.class_name, "Status")
        self.assertEqual(len(parsed.methods), 1)
        self.assertEqual(parsed.methods[0].name, "isActive")

    def test_unsupported_construct_record(self):
        # Java 14+ Record structure. javalang doesn't parse 'record' out of the box in older parser versions,
        # but if it fails with JavaSyntaxError we should raise it, or if it parses, log skipped/unsupported.
        content = """
        public record Point(int x, int y) {}
        """
        filepath = self.write_temp_file(content, "Point.java")
        try:
            self.parser.parse(filepath)
        except javalang.parser.JavaSyntaxError:
            log_msgs = [msg for level, msg in self.log_capture]
            self.assertIn("Syntax error", log_msgs)
            self.assertIn("File skipped: " + filepath, log_msgs)

    def test_generic_methods(self):
        content = """
        public class Util {
            public <T> T identity(T val) {
                return val;
            }
        }
        """
        filepath = self.write_temp_file(content, "Util.java")
        parsed = self.parser.parse(filepath)
        
        self.assertEqual(parsed.class_name, "Util")
        self.assertEqual(len(parsed.methods), 1)
        method = parsed.methods[0]
        self.assertEqual(method.name, "identity")
        self.assertEqual(method.return_type, "T")

    def test_nested_classes(self):
        content = """
        public class Outer {
            public void outerMethod() {}
            
            public static class Inner {
                public void innerMethod() {}
            }
        }
        """
        filepath = self.write_temp_file(content, "Outer.java")
        parsed = self.parser.parse(filepath)
        
        self.assertEqual(parsed.class_name, "Outer")
        # Methods in outer and inner should be extracted
        method_names = [m.name for m in parsed.methods]
        self.assertIn("outerMethod", method_names)
        self.assertIn("innerMethod", method_names)

    def test_empty_class(self):
        content = """
        package com.example;
        public class Empty {}
        """
        filepath = self.write_temp_file(content, "Empty.java")
        parsed = self.parser.parse(filepath)
        self.assertEqual(parsed.class_name, "Empty")
        self.assertEqual(len(parsed.methods), 0)
        self.assertEqual(len(parsed.fields), 0)

    def test_anonymous_class(self):
        content = """
        package com.example;
        public class MyClass {
            public void doSomething() {
                Runnable r = new Runnable() {
                    @Override
                    public void run() {
                        System.out.println("hello");
                    }
                };
            }
        }
        """
        filepath = self.write_temp_file(content, "MyClass.java")
        parsed = self.parser.parse(filepath)
        self.assertEqual(parsed.class_name, "MyClass")
        
        method_names = [m.name for m in parsed.methods]
        self.assertIn("doSomething", method_names)
        self.assertIn("run", method_names)

    def test_invalid_java_syntax(self):
        content = """
        public class BadClass {
            public void incompleteMethod( {
        }
        """
        filepath = self.write_temp_file(content, "BadClass.java")
        with self.assertRaises(javalang.parser.JavaSyntaxError):
            self.parser.parse(filepath)
            
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Syntax error", log_msgs)
        self.assertIn("File skipped: " + filepath, log_msgs)

    def test_integration_against_sample_project(self):
        # Validate that we can parse the real UserService.java, UserController.java, UserRepository.java
        for filename in ["UserService.java", "UserController.java", "UserRepository.java"]:
            path = f"projects/sampleProject/{filename}"
            parsed = self.parser.parse(path)
            self.assertIsNotNone(parsed)
            self.assertEqual(parsed.file_name, filename)
            self.assertIsNotNone(parsed.class_name)
            self.assertTrue(len(parsed.methods) > 0)


if __name__ == "__main__":
    unittest.main()
