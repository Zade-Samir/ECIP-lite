import unittest
import tempfile
import shutil
import logging
import json
from pathlib import Path

from ecip_core.indexing.index_builder import IndexBuilder

class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append((record.levelname, record.getMessage()))


from unittest.mock import patch
from ecip_core.embedding.models.embedding import Embedding

class TestIndexBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = IndexBuilder()
        self.test_dir = tempfile.mkdtemp()
        
        # Configure logging capture
        self.log_handler = LogCaptureHandler()
        self.log_handler.setLevel(logging.DEBUG)
        logging.getLogger("ecip_core.indexing.index_builder").addHandler(self.log_handler)
        self.log_capture = self.log_handler.records
        
        # Patch EmbeddingService.generate to return fake vectors
        self.embedding_patch = patch('ecip_core.embedding.embedding_service.EmbeddingService.generate')
        self.mock_generate = self.embedding_patch.start()
        from ecip_core.inference.config.settings import settings
        self.mock_generate.side_effect = lambda chunk: Embedding(
            file_name=chunk.file_name,
            class_name=chunk.class_name,
            method_name=chunk.method_name or "",
            source_code=chunk.source_code,
            vector=[0.1] * settings.EMBEDDING_DIMENSION
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        logging.getLogger("ecip_core.indexing.index_builder").removeHandler(self.log_handler)
        self.embedding_patch.stop()

    def write_temp_file(self, content: str, filename: str) -> str:
        filepath = Path(self.test_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)

    def test_incremental_indexing(self):
        # 1. Write initial project code
        content = """
        package com.example;
        public class MyService {
            public void test1() {
                System.out.println("Hello 1");
            }
            public void test2() {
                System.out.println("Hello 2");
            }
        }
        """
        filepath = self.write_temp_file(content, "MyService.java")
        
        # First index run
        self.builder.build(self.test_dir)
        
        # Verify cache file exists
        cache_file = Path(self.test_dir) / ".ecip_chunk_cache.json"
        self.assertTrue(cache_file.exists())
        with open(cache_file, "r") as f:
            cache1 = json.load(f)
            
        # Log assertions for first run (should generate hashes since cache was empty)
        log_msgs_1 = [msg for level, msg in self.log_capture]
        self.assertTrue(any("Chunk hash generated" in msg for msg in log_msgs_1))
        
        # Clear logs
        self.log_capture.clear()
        
        # Second run (No changes)
        self.builder.build(self.test_dir)
        with open(cache_file, "r") as f:
            cache2 = json.load(f)
            
        # Assert same hashes
        self.assertEqual(cache1, cache2)
        
        # Log assertions for second run (should find unchanged hashes)
        log_msgs_2 = [msg for level, msg in self.log_capture]
        self.assertTrue(any("Hash unchanged" in msg for msg in log_msgs_2))
        self.assertFalse(any("Hash changed" in msg for msg in log_msgs_2))
        
        # Clear logs
        self.log_capture.clear()
        
        # 3. Modify only one method (test1)
        modified_content = """
        package com.example;
        public class MyService {
            public void test1() {
                System.out.println("Hello 1 MODIFIED!");
            }
            public void test2() {
                System.out.println("Hello 2");
            }
        }
        """
        # Overwrite file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(modified_content)
            
        # Third run (1 changed method)
        self.builder.build(self.test_dir)
        with open(cache_file, "r") as f:
            cache3 = json.load(f)
            
        # Log assertions for third run (should log Hash changed)
        log_msgs_3 = [msg for level, msg in self.log_capture]
        self.assertTrue(any("Hash changed" in msg for msg in log_msgs_3))
        
        # Verify ONLY test1 and overview hash changed (since overview public method list changed too).
        # But test2 hash MUST remain identical!
        # Find chunk IDs
        test1_id = None
        test2_id = None
        for cid, val in cache1.items():
            if val.get("method_name") == "test1":
                test1_id = cid
            elif val.get("method_name") == "test2":
                test2_id = cid
                
        self.assertIsNotNone(test1_id)
        self.assertIsNotNone(test2_id)
        
        # test1 hash changed
        self.assertNotEqual(cache1[test1_id]["content_hash"], cache3[test1_id]["content_hash"])
        # test2 hash unchanged
        self.assertEqual(cache1[test2_id]["content_hash"], cache3[test2_id]["content_hash"])


if __name__ == "__main__":
    unittest.main()
