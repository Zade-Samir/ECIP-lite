import json
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
        java_files = self.scanner.scan(project_path)
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

        for file in java_files:
            logger.info(f"Indexing {file.name}")

            # ---------- Metadata ----------
            parsed = self.parser.parse(str(file))
            self.repository.save(parsed)

            # ---------- Semantic ----------
            chunks = self.chunker.chunk(str(file))

            for chunk in chunks:
                chunk_id = chunk.chunk_id
                content_hash = chunk.content_hash

                # Check if hash has changed
                cached_data = cache.get(chunk_id)
                if cached_data and cached_data.get("content_hash") == content_hash:
                    logger.info("Hash unchanged")
                    vector = cached_data["vector"]
                    embedding = Embedding(
                        file_name=chunk.file_name,
                        class_name=chunk.class_name,
                        method_name=chunk.method_name or "",
                        source_code=chunk.source_code,
                        vector=vector
                    )
                    self.faiss_store.add(embedding)

                    # Carry over to new cache
                    new_cache[chunk_id] = {
                        "content_hash": content_hash,
                        "vector": vector,
                        "method_name": chunk.method_name
                    }
                else:
                    if cached_data:
                        logger.info("Hash changed")
                    else:
                        logger.info("Chunk hash generated")

                    # Generate fresh embedding
                    embedding = self.embedding_service.generate(chunk)
                    self.faiss_store.add(embedding)

                    # Save to new cache
                    new_cache[chunk_id] = {
                        "content_hash": content_hash,
                        "vector": embedding.vector,
                        "method_name": chunk.method_name
                    }

        # Persist new cache for next index build
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(new_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write incremental cache: {e}")

        logger.info("Project indexing completed.")
        return self.faiss_store