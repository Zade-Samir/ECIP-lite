import unittest
import tempfile
import shutil
import logging
import json
import os
from pathlib import Path
from unittest.mock import patch

from ecip_core.indexing.index_builder import IndexBuilder
from ecip_core.embedding.models.embedding import Embedding

class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append((record.levelname, record.getMessage()))


class TestIndexBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = IndexBuilder()
        self.test_dir = tempfile.mkdtemp()
        
        # Configure logging capture
        self.log_handler = LogCaptureHandler()
        self.log_handler.setLevel(logging.DEBUG)
        logging.getLogger("ecip_core.indexing.index_builder").addHandler(self.log_handler)
        logging.getLogger("ecip_core.vectorstore.faiss_store").addHandler(self.log_handler)
        logging.getLogger("ecip_core.storage.sqlite.repository").addHandler(self.log_handler)
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

        # Also patch generate_batch (used by IndexBuilder after Prompt 012)
        self.embedding_batch_patch = patch('ecip_core.embedding.embedding_service.EmbeddingService.generate_batch')
        self.mock_generate_batch = self.embedding_batch_patch.start()
        self.mock_generate_batch.side_effect = lambda chunks: [
            Embedding(
                file_name=chunk.file_name,
                class_name=chunk.class_name,
                method_name=chunk.method_name or "",
                source_code=chunk.source_code,
                vector=[0.1] * settings.EMBEDDING_DIMENSION
            )
            for chunk in chunks
        ]

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        logging.getLogger("ecip_core.indexing.index_builder").removeHandler(self.log_handler)
        logging.getLogger("ecip_core.vectorstore.faiss_store").removeHandler(self.log_handler)
        logging.getLogger("ecip_core.storage.sqlite.repository").removeHandler(self.log_handler)
        self.embedding_patch.stop()
        self.embedding_batch_patch.stop()

    def write_temp_file(self, content: str, filename: str) -> str:
        filepath = Path(self.test_dir) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)

    def test_incremental_indexing_full_pipeline(self):
        # Setup two files
        content_a = "package com.example; public class ServiceA {}"
        content_b = "package com.example; public class ServiceB {}"
        
        path_a = self.write_temp_file(content_a, "ServiceA.java")
        path_b = self.write_temp_file(content_b, "ServiceB.java")
        
        # 1. First run indexes all files (Cold start)
        self.log_capture.clear()
        self.builder.build(self.test_dir)
        
        log_msgs_1 = [msg for level, msg in self.log_capture]
        self.assertTrue(any("Index started" in msg for msg in log_msgs_1))
        self.assertTrue(any("File indexed: ServiceA.java" in msg for msg in log_msgs_1))
        self.assertTrue(any("File indexed: ServiceB.java" in msg for msg in log_msgs_1))
        self.assertTrue(any("Total duration" in msg for msg in log_msgs_1))
        
        # Verify both exist in SQLite DB
        paths_in_db = self.builder.repository.get_all_file_paths()
        self.assertIn(str(Path(path_a).resolve()), paths_in_db)
        self.assertIn(str(Path(path_b).resolve()), paths_in_db)
        
        # 2. Second run skips unchanged files
        self.log_capture.clear()
        builder2 = IndexBuilder()
        builder2.build(self.test_dir)
        
        log_msgs_2 = [msg for level, msg in self.log_capture]
        self.assertTrue(any("File skipped: ServiceA.java" in msg for msg in log_msgs_2))
        self.assertTrue(any("File skipped: ServiceB.java" in msg for msg in log_msgs_2))
        self.assertFalse(any("File indexed:" in msg for msg in log_msgs_2))
        
        # 3. Modify one file (ServiceA)
        self.log_capture.clear()
        content_a_modified = "package com.example; public class ServiceA { public void run() {} }"
        with open(path_a, "w", encoding="utf-8") as f:
            f.write(content_a_modified)
            
        builder3 = IndexBuilder()
        builder3.build(self.test_dir)
        
        log_msgs_3 = [msg for level, msg in self.log_capture]
        self.assertTrue(any("File indexed: ServiceA.java" in msg for msg in log_msgs_3))
        self.assertTrue(any("File skipped: ServiceB.java" in msg for msg in log_msgs_3))
        self.assertTrue(any("Stale vector cleaned" in msg for msg in log_msgs_3))
        
        # 4. Delete one file (ServiceB)
        self.log_capture.clear()
        os.remove(path_b)
        
        builder4 = IndexBuilder()
        builder4.build(self.test_dir)
        
        log_msgs_4 = [msg for level, msg in self.log_capture]
        self.assertTrue(any("File removed" in msg for msg in log_msgs_4))
        self.assertTrue(any("Stale vector cleaned" in msg for msg in log_msgs_4))
        self.assertTrue(any("File skipped: ServiceA.java" in msg for msg in log_msgs_4))
        
        # Verify ServiceB is removed from SQLite DB
        paths_in_db_after_delete = self.builder.repository.get_all_file_paths()
        self.assertNotIn(str(Path(path_b).resolve()), paths_in_db_after_delete)
        self.assertIn(str(Path(path_a).resolve()), paths_in_db_after_delete)


if __name__ == "__main__":
    unittest.main()
