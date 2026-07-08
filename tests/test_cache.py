import os
import time
import unittest
import threading
from tempfile import TemporaryDirectory
from ecip_core.cache.manager import CacheManager, MemoryCache, DiskCache


class TestCache(unittest.TestCase):

    def setUp(self):
        # We initialize local instances to prevent polluting global singleton state
        self.memory_cache = MemoryCache()
        self.disk_dir = TemporaryDirectory()
        self.disk_cache = DiskCache(cache_dir=self.disk_dir.name)
        self.manager = CacheManager(disk_enabled=True)
        self.manager.memory_store = self.memory_cache
        self.manager.disk_store = self.disk_cache
        self.manager.clear()

    def tearDown(self):
        self.manager.clear()
        self.disk_dir.cleanup()

    def test_cache_miss_initially(self):
        """Initial request for a key is a miss and returns None."""
        val = self.manager.get("key1")
        self.assertIsNone(val)
        stats = self.manager.get_stats()
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 0)

    def test_cache_hit_after_set(self):
        """Setting a key and retrieving it results in a cache hit."""
        self.manager.set("key1", "val1")
        
        # First retrieve (hits memory store)
        val = self.manager.get("key1")
        self.assertEqual(val, "val1")
        
        stats = self.manager.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 0)

    def test_ttl_expiration_evicts_entry(self):
        """Cache entry becomes inaccessible and is evicted after TTL expiration."""
        # Write with 1 second TTL
        self.manager.set("exp_key", "exp_val", ttl=1)
        
        # Verify it exists initially
        self.assertEqual(self.manager.get("exp_key"), "exp_val")
        
        # Sleep to let it expire
        time.sleep(1.1)
        
        # Verify it is now a miss
        self.assertIsNone(self.manager.get("exp_key"))

    def test_cache_invalidation_delete(self):
        """Deleting a key removes it from both cache stores, causing subsequent miss."""
        self.manager.set("key_del", "some_data")
        self.assertEqual(self.manager.get("key_del"), "some_data")
        
        self.manager.delete("key_del")
        self.assertIsNone(self.manager.get("key_del"))

    def test_cache_invalidation_clear(self):
        """Clearing the cache evicts all records and resets hits/misses statistics."""
        self.manager.set("k1", "v1")
        self.manager.set("k2", "v2")
        self.assertEqual(self.manager.get("k1"), "v1")
        self.assertEqual(self.manager.get("k2"), "v2")
        
        self.manager.clear()
        stats = self.manager.get_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)

        self.assertIsNone(self.manager.get("k1"))
        self.assertIsNone(self.manager.get("k2"))


    def test_serialization_and_disk_promotion(self):
        """Disk cache preserves complex objects and promotions load back to memory cache."""
        complex_obj = {"list": [1, 2, 3], "nested": {"a": 1}}
        self.manager.set("complex", complex_obj)
        
        # Evict from memory store directly to force disk read promotion
        self.memory_cache.clear()
        
        # Get from manager should load from disk cache, promote to memory, and return it
        val = self.manager.get("complex")
        self.assertEqual(val, complex_obj)
        
        # Check that it got successfully promoted back to memory
        self.assertEqual(self.memory_cache.get("complex"), complex_obj)

    def test_thread_safety_concurrent_access(self):
        """Concurrent threads can read and write to the cache store without corruption."""
        num_threads = 10
        runs_per_thread = 50
        errors = []

        def worker(thread_idx):
            try:
                for i in range(runs_per_thread):
                    key = f"thread_{thread_idx}_run_{i}"
                    val = f"value_{i}"
                    self.manager.set(key, val)
                    self.assertEqual(self.manager.get(key), val)
            except Exception as e:
                errors.append(e)

        threads = []
        for idx in range(num_threads):
            t = threading.Thread(target=worker, args=(idx,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent execution errors detected: {errors}")


if __name__ == "__main__":
    unittest.main()
