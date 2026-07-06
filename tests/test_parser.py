import unittest
import logging
import tempfile
import shutil
import javalang
from pathlib import Path

from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile

logger = logging.getLogger(__name__)


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
        
        self.assertEqual(len(parsed.constructors), 1)
        self.assertEqual(parsed.constructors[0].parameters, ["MyService service"])
        self.assertEqual(parsed.constructors[0].modifiers, ["public"])
        
        self.assertEqual(len(parsed.fields), 1)
        self.assertEqual(parsed.fields[0].name, "service")
        self.assertEqual(parsed.fields[0].type, "MyService")
        self.assertEqual(parsed.fields[0].modifiers, ["private", "final"])
        
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
        self.assertEqual(len(parsed.fields), 1)
        self.assertEqual(parsed.fields[0].name, "id")
        self.assertEqual(parsed.fields[0].type, "Long")
        self.assertEqual(parsed.fields[0].modifiers, ["private"])

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
        self.assertIn("Comparable<BaseInterface>", parsed.interfaces)
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
        parsed_files = {}
        for filename in ["UserService.java", "UserController.java", "UserRepository.java"]:
            path = f"projects/sampleProject/{filename}"
            parsed = self.parser.parse(path)
            self.assertIsNotNone(parsed)
            self.assertEqual(parsed.file_name, filename)
            self.assertIsNotNone(parsed.class_name)
            self.assertTrue(len(parsed.methods) > 0)
            parsed_files[filename] = parsed
            
        # UserController assertions
        controller = parsed_files["UserController.java"]
        self.assertEqual(controller.class_name, "UserController")
        self.assertIn("@RestController", controller.class_annotations)
        self.assertIn("@RequestMapping", controller.class_annotations)
        
        # Verify method mapping annotations
        methods_map = {m.name: m for m in controller.methods}
        self.assertIn("getAllUsers", methods_map)
        self.assertIn("@GetMapping", methods_map["getAllUsers"].annotations)
        self.assertIn("getUser", methods_map)
        self.assertIn("@GetMapping", methods_map["getUser"].annotations)
        
        # Verify dependencies
        self.assertEqual(len(controller.dependencies), 1)
        self.assertEqual(controller.dependencies[0].source_class, "UserController")
        self.assertEqual(controller.dependencies[0].target_class, "UserService")
        self.assertEqual(controller.dependencies[0].injection_type, "FIELD")
        
        # UserService assertions
        service = parsed_files["UserService.java"]
        self.assertEqual(service.class_name, "UserService")
        self.assertIn("@Service", service.class_annotations)
        self.assertEqual(len(service.dependencies), 1)
        self.assertEqual(service.dependencies[0].source_class, "UserService")
        self.assertEqual(service.dependencies[0].target_class, "UserRepository")
        self.assertEqual(service.dependencies[0].injection_type, "FIELD")
        
        # UserRepository assertions
        repository = parsed_files["UserRepository.java"]
        self.assertEqual(repository.class_name, "UserRepository")
        self.assertIn("@Repository", repository.class_annotations)

    def test_serialization_support(self):
        content = """
        package com.example.model;
        
        import java.io.Serializable;
        
        @Entity
        public class User extends BaseEntity implements Serializable, Cloneable {
            private Long id;
            
            public User() {}
            
            public void save() throws IOException, SQLException {}
        }
        """
        filepath = self.write_temp_file(content, "User.java")
        parsed = self.parser.parse(filepath)
        
        # Verify serialization to dict and JSON
        model_dict = parsed.model_dump()
        self.assertEqual(model_dict["class_name"], "User")
        self.assertEqual(model_dict["superclass"], "BaseEntity")
        self.assertEqual(model_dict["implemented_interfaces"], ["Serializable", "Cloneable"])
        
        # Verify fields serialization
        self.assertEqual(len(model_dict["fields"]), 1)
        self.assertEqual(model_dict["fields"][0]["name"], "id")
        self.assertEqual(model_dict["fields"][0]["type"], "Long")
        self.assertEqual(model_dict["fields"][0]["modifiers"], ["private"])
        
        # Verify constructors serialization
        self.assertEqual(len(model_dict["constructors"]), 1)
        self.assertEqual(model_dict["constructors"][0]["modifiers"], ["public"])
        
        # Verify methods throws serialization
        self.assertEqual(len(model_dict["methods"]), 1)
        self.assertEqual(model_dict["methods"][0]["name"], "save")
        self.assertEqual(model_dict["methods"][0]["throws"], ["IOException", "SQLException"])
        
        # Verify Pydantic JSON dumping
        json_data = parsed.model_dump_json()
        self.assertIn('"class_name":"User"', json_data)
        self.assertIn('"throws":["IOException","SQLException"]', json_data)

    def test_dependency_and_annotation_features(self):
        content = """
        package com.example.service;
        
        @Service
        @Transactional
        public class MyService {
            
            @Autowired
            private UserRepository userRepo;
            
            @Value("${app.config.value}")
            private String configValue;
            
            // Unsupported/custom annotation to trigger warning
            @CustomAnnotation
            private int status;
            
            public MyService(EmailService emailService, AuditLogRepository auditRepo) {
                // constructor injection
            }
        }
        """
        filepath = self.write_temp_file(content, "MyService.java")
        parsed = self.parser.parse(filepath)
        
        # Verify class annotations
        self.assertIn("@Service", parsed.class_annotations)
        self.assertIn("@Transactional", parsed.class_annotations)
        
        # Verify fields and their annotations
        field_map = {f.name: f for f in parsed.fields}
        self.assertIn("userRepo", field_map)
        self.assertIn("@Autowired", field_map["userRepo"].annotations)
        
        self.assertIn("configValue", field_map)
        self.assertIn("@Value", field_map["configValue"].annotations)
        
        self.assertIn("status", field_map)
        self.assertIn("@CustomAnnotation", field_map["status"].annotations)
        
        # Verify constructor details
        self.assertEqual(len(parsed.constructors), 1)
        c = parsed.constructors[0]
        self.assertEqual(c.injected_dependency_types, ["EmailService", "AuditLogRepository"])
        self.assertEqual(c.start_line, 18)
        self.assertEqual(c.end_line, 20)
        
        # Verify dependency metadata
        self.assertEqual(len(parsed.dependencies), 4)
        
        # We expect two CONSTRUCTOR dependencies and two FIELD dependencies
        constructor_deps = [d for d in parsed.dependencies if d.injection_type == "CONSTRUCTOR"]
        field_deps = [d for d in parsed.dependencies if d.injection_type == "FIELD"]
        
        self.assertEqual(len(constructor_deps), 2)
        self.assertEqual(len(field_deps), 2)
        
        # Verify constructor dependencies detail
        dep_email = [d for d in constructor_deps if d.target_class == "EmailService"][0]
        self.assertEqual(dep_email.source_class, "MyService")
        self.assertEqual(dep_email.parameter_name, "emailService")
        
        dep_audit = [d for d in constructor_deps if d.target_class == "AuditLogRepository"][0]
        self.assertEqual(dep_audit.source_class, "MyService")
        self.assertEqual(dep_audit.parameter_name, "auditRepo")
        
        # Verify field dependencies detail
        field_targets = [d.target_class for d in field_deps]
        self.assertIn("UserRepository", field_targets)
        self.assertIn("String", field_targets)
        
        # Verify unsupported annotation log warning
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Unsupported annotation: @CustomAnnotation", log_msgs)
        self.assertIn("Dependency discovered", log_msgs)
        self.assertIn("Constructor parsed", log_msgs)

    def test_configuration_class_parsing(self):
        content = """
        package com.example.config;
        
        @Configuration
        public class AppConfig {
            
            @Bean
            public MyService myService() {
                return new MyService();
            }
        }
        """
        filepath = self.write_temp_file(content, "AppConfig.java")
        parsed = self.parser.parse(filepath)
        self.assertEqual(parsed.class_name, "AppConfig")
        self.assertIn("@Configuration", parsed.class_annotations)
        self.assertEqual(len(parsed.methods), 1)
        self.assertEqual(parsed.methods[0].name, "myService")

    def test_negative_scenarios_empty_and_corrupted(self):
        # Empty file
        filepath_empty = self.write_temp_file("", "Empty.java")
        with self.assertRaises(Exception):
            self.parser.parse(filepath_empty)
            
        # Corrupted non-Java file
        filepath_corrupted = self.write_temp_file("Random binary data: \x00\x01\x02", "Corrupted.java")
        with self.assertRaises(Exception):
            self.parser.parse(filepath_corrupted)

    def test_negative_scenario_missing_package(self):
        content = """
        public class NoPackage {
            public void test() {}
        }
        """
        filepath = self.write_temp_file(content, "NoPackage.java")
        parsed = self.parser.parse(filepath)
        self.assertEqual(parsed.class_name, "NoPackage")
        self.assertIsNone(parsed.package_name)

    def test_logging_validation_happy_and_error(self):
        self.log_capture.clear()
        
        content = """
        package com.example;
        public class LoggedClass {}
        """
        filepath = self.write_temp_file(content, "LoggedClass.java")
        self.parser.parse(filepath)
        
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Parsing started", log_msgs)
        self.assertIn("File parsed: LoggedClass.java", log_msgs)
        self.assertIn("Parser mapping complete", log_msgs)
        self.assertTrue(any("Completion summary:" in msg for msg in log_msgs))

    def test_performance_parsing(self):
        # Generate Small File (10 lines)
        small_content = "package test;\npublic class Small {\n  public void hello() {}\n}\n"
        
        # Generate Medium File (100 lines)
        medium_lines = ["package test;", "public class Medium {"]
        for i in range(40):
            medium_lines.append(f"  private int field{i};")
            medium_lines.append(f"  public void method{i}() {{}}")
        medium_lines.append("}")
        medium_content = "\n".join(medium_lines)
        
        # Generate Large File (1000 lines)
        large_lines = ["package test;", "public class Large {"]
        for i in range(400):
            large_lines.append(f"  private int field{i};")
            large_lines.append(f"  public void method{i}() {{}}")
        large_lines.append("}")
        large_content = "\n".join(large_lines)
        
        import time
        
        # Parse Small
        small_path = self.write_temp_file(small_content, "Small.java")
        start_small = time.perf_counter()
        self.parser.parse(small_path)
        end_small = time.perf_counter()
        small_dur = end_small - start_small
        
        # Parse Medium
        medium_path = self.write_temp_file(medium_content, "Medium.java")
        start_medium = time.perf_counter()
        self.parser.parse(medium_path)
        end_medium = time.perf_counter()
        medium_dur = end_medium - start_medium
        
        # Parse Large
        large_path = self.write_temp_file(large_content, "Large.java")
        start_large = time.perf_counter()
        self.parser.parse(large_path)
        end_large = time.perf_counter()
        large_dur = end_large - start_large
        
        # Log performance metrics
        logger.info(f"Performance Test - Small file parsing: {small_dur:.4f}s")
        logger.info(f"Performance Test - Medium file parsing: {medium_dur:.4f}s")
        logger.info(f"Performance Test - Large file parsing: {large_dur:.4f}s")
        
        # Assert sanity checks
        self.assertTrue(small_dur >= 0)
        self.assertTrue(medium_dur >= 0)
        self.assertTrue(large_dur >= 0)


if __name__ == "__main__":
    unittest.main()
