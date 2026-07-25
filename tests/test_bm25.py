import os
import tempfile
import unittest
from ecip_core.search.bm25.bm25 import BM25Index, tokenize


class TestBM25(unittest.TestCase):

    def test_tokenization(self):
        text = "com.example.UserService.getUser"
        tokens = tokenize(text)
        self.assertEqual(tokens, ["com", "example", "user", "service", "get", "user"])

        text_special = "void main(String[] args) {"
        tokens_special = tokenize(text_special)
        self.assertIn("void", tokens_special)
        self.assertIn("main", tokens_special)
        self.assertIn("string", tokens_special)
        self.assertIn("args", tokens_special)

    def test_bm25_fit_and_search(self):
        chunks = [
            {
                "chunk_id": "chunk_1",
                "content": "public class UserService { public User getUser(String id) { return null; } }",
                "file_path": "UserService.java"
            },
            {
                "chunk_id": "chunk_2",
                "content": "public class OrderService { public Order getOrder(String id) { return null; } }",
                "file_path": "OrderService.java"
            }
        ]

        index = BM25Index()
        index.fit(chunks)

        # Search for exact match
        results = index.search("UserService", k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["chunk_id"], "chunk_1")  # chunk_1 contains 'UserService'

        results_order = index.search("getOrder", k=2)
        self.assertEqual(results_order[0]["chunk_id"], "chunk_2")

    def test_save_and_load(self):
        chunks = [
            {
                "chunk_id": "chunk_1",
                "content": "public class UserService {}",
                "file_path": "UserService.java"
            }
        ]
        index = BM25Index()
        index.fit(chunks)

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "bm25_index.json")
            index.save(file_path)

            loaded_index = BM25Index()
            loaded_index.load(file_path)

            self.assertEqual(loaded_index.total_docs, 1)
            self.assertEqual(loaded_index.avg_doc_len, index.avg_doc_len)
            
            # Verify search works on loaded index
            results = loaded_index.search("UserService", k=1)
            self.assertEqual(results[0]["chunk_id"], "chunk_1")


if __name__ == "__main__":
    unittest.main()
