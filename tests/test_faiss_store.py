import unittest
import tempfile
import shutil
import math
from pathlib import Path
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.embedding.models.embedding import Embedding
from ecip_core.inference.config.settings import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DIM = settings.EMBEDDING_DIMENSION


def make_vector(value: float = 1.0, dim: int = DIM) -> list[float]:
    """Return a normalised vector of given dimension."""
    raw = [value] * dim
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


def make_embedding(
    file_name: str = "MyClass.java",
    class_name: str = "MyClass",
    method_name: str = "myMethod",
    source_code: str = "void myMethod() {}",
    vector_value: float = 1.0,
) -> Embedding:
    return Embedding(
        file_name=file_name,
        class_name=class_name,
        method_name=method_name,
        source_code=source_code,
        vector=make_vector(vector_value),
    )


class TestFAISSStore(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.index_path = str(Path(self.tmp_dir) / "faiss.index")
        self.metadata_path = str(Path(self.tmp_dir) / "faiss_metadata.json")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def make_store(self) -> FAISSStore:
        """Helper: fresh store with temp paths."""
        return FAISSStore(
            index_path=self.index_path,
            metadata_path=self.metadata_path,
        )

    # -----------------------------------------------------------------------
    # Cold start
    # -----------------------------------------------------------------------

    def test_create_fresh_index(self):
        store = self.make_store()
        self.assertEqual(store.vector_count(), 0)
        self.assertEqual(len(store.metadata), 0)

    # -----------------------------------------------------------------------
    # Add
    # -----------------------------------------------------------------------

    def test_add_single_vector(self):
        store = self.make_store()
        emb = make_embedding()
        store.add(emb)
        self.assertEqual(store.vector_count(), 1)
        self.assertEqual(len(store.metadata), 1)

    def test_add_multiple_vectors(self):
        store = self.make_store()
        for i in range(5):
            store.add(make_embedding(method_name=f"method{i}"))
        self.assertEqual(store.vector_count(), 5)

    def test_add_dimension_mismatch_raises(self):
        store = self.make_store()
        bad_emb = Embedding(
            file_name="A.java",
            class_name="A",
            method_name="m",
            source_code="void m(){}",
            vector=[0.1] * (DIM - 5),
        )
        with self.assertRaises(ValueError):
            store.add(bad_emb)

    # -----------------------------------------------------------------------
    # Persistence — save & load
    # -----------------------------------------------------------------------

    def test_save_creates_files(self):
        store = self.make_store()
        store.add(make_embedding())
        self.assertTrue(Path(self.index_path).exists())
        self.assertTrue(Path(self.metadata_path).exists())

    def test_reload_preserves_vector_count(self):
        # Build and persist
        store1 = self.make_store()
        store1.add(make_embedding(method_name="m1"))
        store1.add(make_embedding(method_name="m2"))
        self.assertEqual(store1.vector_count(), 2)

        # Reload from disk
        store2 = self.make_store()
        self.assertEqual(store2.vector_count(), 2)

    def test_reload_preserves_metadata(self):
        store1 = self.make_store()
        store1.add(make_embedding(method_name="targetMethod"))

        store2 = self.make_store()
        self.assertEqual(len(store2.metadata), 1)
        self.assertEqual(store2.metadata[0].method_name, "targetMethod")

    def test_corrupt_index_falls_back_to_empty(self):
        # Write garbage to the index file
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.index_path).write_bytes(b"garbage_data")
        Path(self.metadata_path).write_text("[]")

        store = self.make_store()
        self.assertEqual(store.vector_count(), 0)

    # -----------------------------------------------------------------------
    # Search
    # -----------------------------------------------------------------------

    def test_search_returns_results(self):
        store = self.make_store()
        store.add(make_embedding(method_name="findUser"))
        store.add(make_embedding(method_name="deleteUser"))

        results = store.search(make_vector(), k=2)
        self.assertEqual(len(results), 2)

    def test_search_empty_index_returns_empty(self):
        store = self.make_store()
        results = store.search(make_vector(), k=3)
        self.assertEqual(results, [])

    def test_search_dimension_mismatch_raises(self):
        store = self.make_store()
        with self.assertRaises(ValueError):
            store.search([0.1] * (DIM - 3), k=1)

    def test_search_top_k_respected(self):
        store = self.make_store()
        for i in range(10):
            store.add(make_embedding(method_name=f"m{i}"))
        results = store.search(make_vector(), k=3)
        self.assertLessEqual(len(results), 3)

    # -----------------------------------------------------------------------
    # Delete / remove_file
    # -----------------------------------------------------------------------

    def test_remove_file_clears_vectors(self):
        store = self.make_store()
        store.add(make_embedding(file_name="ToDelete.java"))
        store.add(make_embedding(file_name="ToKeep.java"))
        self.assertEqual(store.vector_count(), 2)

        store.remove_file("ToDelete.java")
        self.assertEqual(store.vector_count(), 1)
        self.assertEqual(store.metadata[0].file_name, "ToKeep.java")

    def test_remove_nonexistent_file_is_noop(self):
        store = self.make_store()
        store.add(make_embedding(file_name="Keep.java"))
        store.remove_file("DoesNotExist.java")
        self.assertEqual(store.vector_count(), 1)

    # -----------------------------------------------------------------------
    # Metadata consistency after reload + remove
    # -----------------------------------------------------------------------

    def test_metadata_consistent_after_reload_and_remove(self):
        store1 = self.make_store()
        store1.add(make_embedding(file_name="A.java", method_name="alpha"))
        store1.add(make_embedding(file_name="B.java", method_name="beta"))

        # Reload
        store2 = self.make_store()
        store2.remove_file("A.java")

        # Reload again — must still see only B.java
        store3 = self.make_store()
        self.assertEqual(store3.vector_count(), 1)
        self.assertEqual(store3.metadata[0].method_name, "beta")

    # -----------------------------------------------------------------------
    # In-memory store (no paths)
    # -----------------------------------------------------------------------

    def test_in_memory_store_no_persistence(self):
        store = FAISSStore()
        store.add(make_embedding())
        self.assertEqual(store.vector_count(), 1)
        # No files should be created
        self.assertFalse(Path(self.index_path).exists())


if __name__ == "__main__":
    unittest.main()
