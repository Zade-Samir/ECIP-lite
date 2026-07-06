import unittest
import tempfile
import shutil
import logging
import hashlib
from pathlib import Path

from ecip_core.chunking.java_chunker import JavaChunker

# Set up test logging capture
class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append((record.levelname, record.getMessage()))


class TestJavaChunker(unittest.TestCase):

    def setUp(self):
        self.chunker = JavaChunker()
        self.test_dir = tempfile.mkdtemp()
        
        # Configure logging capture
        self.log_handler = LogCaptureHandler()
        self.log_handler.setLevel(logging.DEBUG)
        logging.getLogger("ecip_core.chunking.java_chunker").addHandler(self.log_handler)
        self.log_capture = self.log_handler.records

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        logging.getLogger("ecip_core.chunking.java_chunker").removeHandler(self.log_handler)

    def write_temp_file(self, content: str, filename: str) -> str:
        filepath = Path(self.test_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)

    def test_happy_path_class_and_methods(self):
        content = """
        package com.example;
        
        @RestController
        public class MyController {
            
            private final MyService service;
            
            public MyController(MyService service) {
                this.service = service;
            }
            
            public void handle() {
                System.out.println("Handling request");
            }
        }
        """
        filepath = self.write_temp_file(content, "MyController.java")
        chunks = self.chunker.chunk(filepath, project_id="my_project")
        
        # 1 Overview chunk + 1 Method chunk = 2 chunks total
        self.assertEqual(len(chunks), 2)
        
        overview = [c for c in chunks if c.chunk_type == "CLASS_OVERVIEW"][0]
        methods = [c for c in chunks if c.chunk_type == "METHOD"]
        
        # Check Overview Chunk
        self.assertIsNone(overview.method_name)
        self.assertEqual(overview.class_name, "MyController")
        self.assertEqual(overview.project_id, "my_project")
        self.assertIn("package com.example;", overview.content)
        self.assertIn("@RestController", overview.content)
        self.assertIn("MyController(MyService service)", overview.content)
        self.assertIn("private final MyService service", overview.content)
        self.assertIn("Public Methods:", overview.content)
        self.assertIn("- public void handle()", overview.content)
        
        # Check Method Chunks
        self.assertEqual(len(methods), 1)
        method_names = [m.method_name for m in methods]
        self.assertIn("handle", method_names)
        
        handle_chunk = [m for m in methods if m.method_name == "handle"][0]
        self.assertIn("public void handle() {", handle_chunk.content)
        self.assertEqual(handle_chunk.start_line, 13)
        self.assertEqual(handle_chunk.end_line, 15)
        
        # Verify Stable Deterministic Chunk IDs, Content Hashes, and Serialization
        for c in chunks:
            self.assertIsNotNone(c.chunk_id)
            self.assertIsNotNone(c.content_hash)
            self.assertIsNone(c.created_at)
            
            # Content Hash correctness
            from ecip_core.chunking.java_chunker import normalize_content
            expected_hash = hashlib.sha256(normalize_content(c.content).encode("utf-8")).hexdigest()
            self.assertEqual(c.content_hash, expected_hash)
            
            # Serialization verification
            json_dump = c.model_dump_json()
            self.assertIn('"chunk_id":', json_dump)
            self.assertIn('"content_hash":', json_dump)

        # Logging assertions
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Chunking started", log_msgs)
        self.assertIn("Overview chunk generated", log_msgs)
        self.assertIn("Overview chunk created", log_msgs)
        self.assertIn("Method chunk created", log_msgs)
        self.assertIn("Chunk validation complete", log_msgs)
        self.assertIn("Total chunks generated: 2", log_msgs)

    def test_edge_case_empty_class(self):
        content = """
        package com.example;
        public class Empty {}
        """
        filepath = self.write_temp_file(content, "Empty.java")
        chunks = self.chunker.chunk(filepath)
        
        self.assertEqual(len(chunks), 1)
        overview = chunks[0]
        self.assertEqual(overview.chunk_type, "CLASS_OVERVIEW")
        
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Empty class", log_msgs)

    def test_edge_case_interface_abstract_methods(self):
        content = """
        package com.example;
        public interface MyInterface {
            void doSomething();
        }
        """
        filepath = self.write_temp_file(content, "MyInterface.java")
        chunks = self.chunker.chunk(filepath)
        
        self.assertEqual(len(chunks), 2)
        
        methods = [c for c in chunks if c.chunk_type == "METHOD"]
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0].method_name, "doSomething")
        self.assertEqual(methods[0].start_line, methods[0].end_line)
        
        log_msgs = [msg for level, msg in self.log_capture]
        self.assertIn("Empty method body", log_msgs)

    def test_integration_against_sample_project(self):
        controller_path = "projects/sampleProject/UserController.java"
        controller_chunks = self.chunker.chunk(controller_path)
        self.assertEqual(len(controller_chunks), 3)
        
        service_path = "projects/sampleProject/UserService.java"
        service_chunks = self.chunker.chunk(service_path)
        self.assertEqual(len(service_chunks), 3)
        
        repo_path = "projects/sampleProject/UserRepository.java"
        repo_chunks = self.chunker.chunk(repo_path)
        self.assertEqual(len(repo_chunks), 3)

        total_chunks = len(controller_chunks) + len(service_chunks) + len(repo_chunks)
        self.assertEqual(total_chunks, 9)
        
        chunk_ids = [c.chunk_id for c in controller_chunks + service_chunks + repo_chunks]
        self.assertEqual(len(chunk_ids), len(set(chunk_ids)))

    def test_whitespace_cleaning(self):
        content = """
        package com.example;
        
        
        
        public class Clean {
            
            public void test() {   
                System.out.println("Hello");   
            }
            
            
            
            
            public void test2() {}
        }
        """
        filepath = self.write_temp_file(content, "Clean.java")
        chunks = self.chunker.chunk(filepath)
        
        methods = [c for c in chunks if c.chunk_type == "METHOD"]
        self.assertEqual(len(methods), 2)
        
        test_method = [m for m in methods if m.method_name == "test"][0]
        # Verify that trailing spaces were stripped but leading spaces were preserved
        self.assertIn('                System.out.println("Hello");', test_method.content)
        self.assertNotIn('Hello");   ', test_method.content)
        
        # Verify that consecutive blank lines were collapsed
        # Total blank lines between test() and test2() should be collapsed
        self.assertNotIn("\n\n\n\n", test_method.content)


    def test_hash_normalization_comments_and_whitespace(self):
        # 1. Base Class Content
        content1 = """
        package com.example;
        public class MyService {
            // This is a comment
            public void execute() {
                /* block comment */
                System.out.println("Executing...");
            }
        }
        """
        
        # 2. Content with whitespace changes and modified comments
        content2 = """
        package com.example;
        public class MyService {
            
            // This is a DIFFERENT comment!
            public void execute() {
                
                System.out.println("Executing...");   
                
            }
        }
        """
        
        # 3. Content with actual semantic code change
        content3 = """
        package com.example;
        public class MyService {
            public void execute() {
                System.out.println("Executing DIFFERENT code...");
            }
        }
        """
        
        path1 = self.write_temp_file(content1, "MyService1.java")
        path2 = self.write_temp_file(content2, "MyService2.java")
        path3 = self.write_temp_file(content3, "MyService3.java")
        
        chunks1 = self.chunker.chunk(path1)
        chunks2 = self.chunker.chunk(path2)
        chunks3 = self.chunker.chunk(path3)
        
        method1 = [c for c in chunks1 if c.chunk_type == "METHOD" and c.method_name == "execute"][0]
        method2 = [c for c in chunks2 if c.chunk_type == "METHOD" and c.method_name == "execute"][0]
        method3 = [c for c in chunks3 if c.chunk_type == "METHOD" and c.method_name == "execute"][0]
        
        # Assert same content hash for comment/whitespace edits
        self.assertEqual(method1.content_hash, method2.content_hash)
        
        # Assert different content hash for semantic changes
        self.assertNotEqual(method1.content_hash, method3.content_hash)


if __name__ == "__main__":
    unittest.main()
