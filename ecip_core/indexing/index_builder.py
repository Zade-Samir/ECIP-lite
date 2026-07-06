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
    Uses persistent FAISS index stored inside the project's .ecip/ directory.
    """

    def __init__(self):
        self.scanner = ProjectScanner()
        self.parser = JavaParser()
        self.repository = JavaRepository()
        self.chunker = JavaChunker()
        self.embedding_service = EmbeddingService()
        # FAISSStore is initialized without paths here; paths are set per build()
        self.faiss_store: FAISSStore | None = None

    def build(self, project_path: str) -> FAISSStore:
        start_time = time.perf_counter()
        logger.info("Index started")

        ecip_dir = Path(project_path) / ".ecip"
        index_path = str(ecip_dir / "faiss.index")
        metadata_path = str(ecip_dir / "faiss_metadata.json")

        # Initialize (or reload) the persistent FAISS store for this project
        self.faiss_store = FAISSStore(
            index_path=index_path,
            metadata_path=metadata_path,
        )

        try:
            java_files = self.scanner.scan(project_path)
        except Exception as e:
            logger.error("Database failure")
            raise e

        logger.info(f"Found {len(java_files)} Java files")

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
                # Vectors for this file are already in the persisted FAISS index
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
                batch_count = max(
                    1,
                    (len(chunks) + self.embedding_service.batch_size - 1)
                    // self.embedding_service.batch_size,
                )
                stats["total_chunks"] += len(chunks)
                stats["total_batches"] += batch_count

                for embedding in embeddings:
                    self.faiss_store.add(embedding)

        duration = time.perf_counter() - start_time
        logger.info(f"Total duration: {duration:.4f}s")

        # Summary report
        print(f"\n--- Indexing Summary Report ---")
        print(f"Files Skipped:   {stats['skipped']}")
        print(f"Files Indexed:   {stats['indexed']}")
        print(f"Files Removed:   {stats['removed']}")
        print(f"Chunks Embedded: {stats['total_chunks']} (in {stats['total_batches']} batches)")
        print(f"Total Duration:  {duration:.4f}s\n")

        return self.faiss_store