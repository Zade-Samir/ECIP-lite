import time
import pickle
import hashlib
import logging
import threading
from pathlib import Path
from functools import wraps
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Callable

from ecip_core.logging import get_logger

logger = get_logger(__name__)


# ─── Cache Abstraction ──────────────────────────────────────────────────

class BaseCache(ABC):
    """
    Abstract base class defining the standard caching interface.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache. Returns None on miss or expiry."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Write a value to the cache with an optional TTL (in seconds)."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a specific key from the cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Evict all entries from this cache store."""
        pass


# ─── Memory Cache Implementation ───────────────────────────────────────

class MemoryCache(BaseCache):
    """
    In-memory cache using a dictionary with thread-safe access locks.
    """

    def __init__(self):
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            val, expires_at = entry
            if time.time() > expires_at:
                logger.warning(f"Expired cache entry: key={key}")
                # Lazy eviction
                self._store.pop(key, None)
                return None
            return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        # Default to 1 hour if not specified
        life = ttl if ttl is not None else 3600
        expires_at = time.time() + life
        with self._lock:
            self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# ─── Disk Cache Implementation ─────────────────────────────────────────

class DiskCache(BaseCache):
    """
    Persistent disk cache storing serialized Python objects under .ecip/cache/.
    Uses pickle to handle complex object serialization.
    """

    def __init__(self, cache_dir: str = ".ecip/cache"):
        self.cache_dir = Path(cache_dir)
        self._lock = threading.Lock()
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Cache initialization failure: could not create dir {cache_dir}: {e}")

    def _get_file_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.cache"

    def get(self, key: str) -> Optional[Any]:
        file_path = self._get_file_path(key)
        with self._lock:
            if not file_path.exists():
                return None

            try:
                with open(file_path, "rb") as f:
                    data = pickle.load(f)

                # Format inside file: (value, expires_at)
                val, expires_at = data
                if time.time() > expires_at:
                    logger.warning(f"Expired cache entry: key={key}")
                    # Evict file
                    try:
                        file_path.unlink()
                    except OSError:
                        pass
                    return None
                return val

            except Exception as e:
                logger.error(f"Cache corruption: failed to read or parse cache file {file_path}: {e}")
                return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        file_path = self._get_file_path(key)
        life = ttl if ttl is not None else 3600
        expires_at = time.time() + life

        with self._lock:
            try:
                # Ensure cache directory still exists (edge case: directory deleted)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                with open(file_path, "wb") as f:
                    pickle.dump((value, expires_at), f)
            except Exception as e:
                logger.error(f"Cache write failure: failed to persist key {key} to {file_path}: {e}")

    def delete(self, key: str) -> None:
        file_path = self._get_file_path(key)
        with self._lock:
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError as e:
                    logger.error(f"Cache delete failure for {key}: {e}")

    def clear(self) -> None:
        with self._lock:
            if self.cache_dir.exists():
                for file_path in self.cache_dir.glob("*.cache"):
                    try:
                        file_path.unlink()
                    except OSError:
                        pass


# ─── Central Cache Manager ─────────────────────────────────────────────

class CacheManager:
    """
    Central Cache Registry. Coordinates Memory and optional Disk cache layers.
    Exposes hits/misses metrics and handles profile-based configuration controls.
    """

    def __init__(self, disk_enabled: bool = True):
        self.memory_store = MemoryCache()
        self.disk_store = DiskCache() if disk_enabled else None
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self._stats_lock = threading.Lock()

        logger.info("Cache initialized")

    def _is_cache_enabled(self) -> bool:
        try:
            from ecip_core.settings import settings
            return settings.CACHE_ENABLED
        except Exception:
            return True

    def _get_default_ttl(self) -> int:
        try:
            from ecip_core.settings import settings
            return settings.CACHE_TTL_SECONDS
        except Exception:
            return 3600

    def get(self, key: str) -> Optional[Any]:
        """Tries to retrieve value from memory cache first, then disk cache."""
        if not self._is_cache_enabled():
            return None

        # Check Memory Cache
        val = self.memory_store.get(key)
        if val is not None:
            with self._stats_lock:
                self.hits += 1
            logger.info(f"Cache hit: {key} (memory)")
            return val

        # Check Disk Cache
        if self.disk_store:
            val = self.disk_store.get(key)
            if val is not None:
                # Cache hot promotion: write back to memory cache
                ttl = self._get_default_ttl()
                self.memory_store.set(key, val, ttl=ttl)
                with self._stats_lock:
                    self.hits += 1
                logger.info(f"Cache hit: {key} (disk)")
                return val

        with self._stats_lock:
            self.misses += 1
        logger.info(f"Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Writes value to memory and disk caches simultaneously."""
        if not self._is_cache_enabled():
            return

        life = ttl if ttl is not None else self._get_default_ttl()
        self.memory_store.set(key, value, ttl=life)
        if self.disk_store:
            self.disk_store.set(key, value, ttl=life)

    def delete(self, key: str) -> None:
        """Invalidates key across memory and disk caches."""
        self.memory_store.delete(key)
        if self.disk_store:
            self.disk_store.delete(key)
        logger.info(f"Cache invalidated: {key}")

    def clear(self) -> None:
        """Evicts everything across all cache tiers."""
        self.memory_store.clear()
        if self.disk_store:
            self.disk_store.clear()
        with self._stats_lock:
            self.hits = 0
            self.misses = 0
        logger.info("Cache invalidated: clear all completed")

    def get_stats(self) -> Dict[str, int]:
        with self._stats_lock:
            return {"hits": self.hits, "misses": self.misses}

    # ─── Decorator & Dynamic Monkey-Patch wrapper ──────────────────────────

    def cached(self, ttl: Optional[int] = None):
        """
        Decorator to transparently cache return values of functions/methods.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Skip self in arguments representation for deterministic cache keying
                filtered_args = args[1:] if args and hasattr(args[0], "__class__") else args

                # Standardize serialization for keys
                arg_strs = []
                for arg in filtered_args:
                    if hasattr(arg, "model_dump_json"):
                        arg_strs.append(arg.model_dump_json())
                    else:
                        arg_strs.append(repr(arg))

                kwarg_strs = []
                for k, v in sorted(kwargs.items()):
                    if hasattr(v, "model_dump_json"):
                        kwarg_strs.append(f"{k}:{v.model_dump_json()}")
                    else:
                        kwarg_strs.append(f"{k}:{repr(v)}")

                raw_string = f"{func.__module__}.{func.__name__}:{','.join(arg_strs)}:{','.join(kwarg_strs)}"
                key = hashlib.md5(raw_string.encode("utf-8")).hexdigest()

                cached_val = self.get(key)
                if cached_val is not None:
                    return cached_val

                # Execute original function and cache result
                result = func(*args, **kwargs)
                self.set(key, result, ttl=ttl)
                return result

            return wrapper
        return decorator


def apply_cache_patches():
    """
    Dynamically applies caching wrapper decorators to target pipeline services.
    Integrates caching without modifying business logic files.
    """
    try:
        import ecip_core.embedding.embedding_service as emb_svc
        emb_svc.EmbeddingService.embed_question = cache_manager.cached()(emb_svc.EmbeddingService.embed_question)
        emb_svc.EmbeddingService.generate = cache_manager.cached()(emb_svc.EmbeddingService.generate)
        logger.info("Caching patch applied: EmbeddingService")
    except Exception as e:
        logger.warning(f"Could not patch EmbeddingService: {e}")

    try:
        import ecip_core.inference.inference_service as inf_svc
        inf_svc.InferenceService.ask = cache_manager.cached()(inf_svc.InferenceService.ask)
        logger.info("Caching patch applied: InferenceService")
    except Exception as e:
        logger.warning(f"Could not patch InferenceService: {e}")

    try:
        import ecip_core.retrieval.hybrid_retrieval as hyb_ret
        hyb_ret.HybridRetrieval.retrieve = cache_manager.cached()(hyb_ret.HybridRetrieval.retrieve)
        logger.info("Caching patch applied: HybridRetrieval")
    except Exception as e:
        logger.warning(f"Could not patch HybridRetrieval: {e}")

    try:
        import ecip_core.retrieval.context.context_builder as ctx_bld
        ctx_bld.ContextBuilder.build = cache_manager.cached()(ctx_bld.ContextBuilder.build)
        logger.info("Caching patch applied: ContextBuilder")
    except Exception as e:
        logger.warning(f"Could not patch ContextBuilder: {e}")

    try:
        import ecip_core.prompt.prompt_builder as prt_bld
        prt_bld.PromptBuilder.build_prompt = cache_manager.cached()(prt_bld.PromptBuilder.build_prompt)
        logger.info("Caching patch applied: PromptBuilder")
    except Exception as e:
        logger.warning(f"Could not patch PromptBuilder: {e}")

    try:
        import ecip_core.retrieval.semantic_search as sem_sch
        sem_sch.SemanticSearch.search = cache_manager.cached()(sem_sch.SemanticSearch.search)
        logger.info("Caching patch applied: SemanticSearch")
    except Exception as e:
        logger.warning(f"Could not patch SemanticSearch: {e}")


# Initialize global default cache manager singleton
cache_manager = CacheManager()


# Run cache monkey patching on load only if cache is enabled and not in a test environment
try:
    import sys
    import os
    from ecip_core.settings import settings
    
    is_testing = (
        settings.ECIP_PROFILE == "testing"
        or (len(sys.argv) > 0 and any(p in os.path.basename(sys.argv[0]) for p in ["unittest", "pytest"]))
    )
    
    if settings.CACHE_ENABLED and not is_testing:
        apply_cache_patches()
except Exception as e:
    pass


