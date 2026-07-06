import json
import hashlib
import time
from pathlib import Path
from ecip_core.scanner.project_scanner import ProjectScanner
from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.storage.sqlite.repository import JavaRepository

from ecip_core.chunking.java_chunker import JavaChunker
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.embedding.models.embedding import Embedding

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class IndexBuilder:
    """
    Builds the ECIP knowledge index for an entire project.
    """

    def __init__(self):
        self.scanner = ProjectScanner()
        self.parser = JavaParser()
        self.repository = JavaRepository()
        self.chunker = JavaChunker()
        self.embedding_service = EmbeddingService()
        self.faiss_store = FAISSStore()

    def build(self, project_path: str) -> FAISSStore:
        start_time = time.perf_counter()
        logger.info("Index started")

        try:
            java_files = self.scanner.scan(project_path)
        except Exception as e:
            logger.error("Database failure")
            raise e

        logger.info(f"Found {len(java_files)} Java files")

        # Load previous hashes/embeddings cache from .ecip_chunk_cache.json if exists
        cache_file = Path(project_path) / ".ecip_chunk_cache.json"
        cache = {}
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load incremental cache: {e}")
                cache = {}

        new_cache = {}

        stats = {
            "skipped": 0,
            "indexed": 0,
            "removed": 0,
            "total_chunks": 0,
            "total_batches": 0,
        }

        # 1. Identify active file paths and calculate current hashes
        active_files = {}
        for file in java_files:
            file_path_str = str(file.resolve())
            try:
                with open(file, "rb") as f:
                    curr_hash = hashlib.sha256(f.read()).hexdigest()
                active_files[file_path_str] = curr_hash
            except Exception as e:
                logger.error("Hash failure")
                raise e

        # 2. Clean up deleted files from SQLite and FAISS
        try:
            db_file_paths = self.repository.get_all_file_paths()
        except Exception as e:
            logger.error("Database failure")
            raise e

        deleted_file_paths = [p for p in db_file_paths if p not in active_files]
        for p in deleted_file_paths:
            self.repository.delete_by_file_path(p)
            self.faiss_store.remove_file(p)
            stats["removed"] += 1

        # 3. Process active files
        for file in java_files:
            file_path_str = str(file.resolve())
            curr_hash = active_files[file_path_str]

            # Get stored hash from database
            stored_hash = self.repository.get_file_hash(file_path_str)

            if stored_hash == curr_hash:
                logger.info(f"File skipped: {file.name}")
                stats["skipped"] += 1

                # Carry over unchanged cache entries and add to FAISS index
                for chunk_id, cached_val in cache.items():
                    if cached_val.get("file_path") == file_path_str:
                        new_cache[chunk_id] = cached_val
                        vector = cached_val["vector"]
                        embedding = Embedding(
                            file_name=cached_val.get("file_name", file.name),
                            class_name=cached_val.get("class_name", "Unknown"),
                            method_name=cached_val.get("method_name") or "",
                            source_code=cached_val.get("source_code", ""),
                            vector=vector
                        )
                        self.faiss_store.add(embedding)
            else:
                logger.info(f"File indexed: {file.name}")
                stats["indexed"] += 1

                # If this is a modified file, remove its stale vectors first
                if stored_hash:
                    self.faiss_store.remove_file(file_path_str)

                # Re-parse changed file
                try:
                    parsed = self.parser.parse(file_path_str)
                except Exception as e:
                    logger.error("Database failure")
                    raise e

                # Save metadata and file_hash in database
                self.repository.save(parsed, file_hash=curr_hash)

                # Re-chunk changed file
                try:
                    chunks = self.chunker.chunk(file_path_str)
                except Exception as e:
                    logger.error("FAISS update failure")
                    raise e

                # Generate embeddings in batch for all chunks of this file
                embeddings = self.embedding_service.generate_batch(chunks)
                batch_count = max(1, (len(chunks) + self.embedding_service.batch_size - 1) // self.embedding_service.batch_size)
                stats["total_chunks"] += len(chunks)
                stats["total_batches"] += batch_count

                for chunk, embedding in zip(chunks, embeddings):
                    self.faiss_store.add(embedding)
                    new_cache[chunk.chunk_id] = {
                        "content_hash": chunk.content_hash,
                        "vector": embedding.vector,
                        "method_name": chunk.method_name,
                        "file_path": file_path_str,
                        "file_name": chunk.file_name,
                        "class_name": chunk.class_name,
                        "source_code": chunk.source_code
                    }

        # Persist new cache for next index build
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(new_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write incremental cache: {e}")

        duration = time.perf_counter() - start_time
        logger.info(f"Total duration: {duration:.4f}s")

        # Summary report
        print(f"\n--- Indexing Summary Report ---")
        print(f"Files Skipped:  {stats['skipped']}")
        print(f"Files Indexed:  {stats['indexed']}")
        print(f"Files Removed:  {stats['removed']}")
        print(f"Chunks Embedded: {stats['total_chunks']} (in {stats['total_batches']} batches)")
        print(f"Total Duration: {duration:.4f}s\n")

        return self.faiss_store