import time
from ecip_core.chunking.code_chunk import CodeChunk
from ecip_core.embedding.models.embedding import Embedding
from ecip_core.embedding.embedding_provider import EmbeddingProvider
from ecip_core.embedding.exceptions import EmbeddingError, InvalidVectorError
from ecip_core.embedding.providers.ollama_embedding_provider import (
    OllamaEmbeddingProvider,
)
from ecip_core.inference.config.settings import settings
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Coordinates embedding generation using the configured provider.
    Supports both single-item and efficient batch processing.
    """

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        batch_size: int | None = None,
    ):
        self.provider = provider or OllamaEmbeddingProvider()
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE

    # ------------------------------------------------------------------
    # Single-item API (backward compatible)
    # ------------------------------------------------------------------

    def generate(self, chunk: CodeChunk) -> Embedding:
        vector = self.provider.embed(chunk.source_code)
        return Embedding(
            file_name=chunk.file_name,
            class_name=chunk.class_name,
            method_name=chunk.method_name or "",
            source_code=chunk.source_code,
            vector=vector,
        )

    def embed_question(self, question: str) -> list[float]:
        return self.provider.embed(question)

    # ------------------------------------------------------------------
    # Batch API
    # ------------------------------------------------------------------

    def generate_batch(self, chunks: list[CodeChunk]) -> list[Embedding]:
        """
        Generate embeddings for a list of chunks efficiently.

        - If the provider supports batching, sends chunks in configurable batches.
        - Falls back to sequential single-item calls if provider doesn't support batch.
        - Preserves original chunk order in the returned list.
        """
        if not chunks:
            return []

        start_time = time.perf_counter()
        logger.info(f"Batch started: {len(chunks)} chunks (batch_size={self.batch_size})")

        embeddings: list[Embedding] = []

        if self.provider.supports_batch():
            embeddings = self._process_in_batches(chunks)
        else:
            logger.info("Sequential fallback: provider does not support batch")
            embeddings = self._process_sequentially(chunks)

        duration = time.perf_counter() - start_time
        logger.info(f"Total embeddings: {len(embeddings)}")
        logger.info(f"Total duration: {duration:.4f}s")

        return embeddings

    def _process_in_batches(self, chunks: list[CodeChunk]) -> list[Embedding]:
        """Split chunks into batches and send each batch to the provider."""
        embeddings: list[Embedding] = []
        total = len(chunks)

        for start in range(0, total, self.batch_size):
            batch = chunks[start: start + self.batch_size]
            texts = [c.source_code for c in batch]

            logger.info(f"Batch completed: items {start + 1}–{start + len(batch)} of {total}")

            try:
                vectors = self.provider.embed_batch(texts)
            except Exception as e:
                logger.error(f"Batch failure: {e}")
                raise

            if len(vectors) != len(batch):
                logger.error(
                    f"Invalid vector count: expected {len(batch)}, got {len(vectors)}"
                )
                raise InvalidVectorError(
                    f"Provider returned {len(vectors)} vectors for batch of {len(batch)}."
                )

            for chunk, vector in zip(batch, vectors):
                embeddings.append(
                    Embedding(
                        file_name=chunk.file_name,
                        class_name=chunk.class_name,
                        method_name=chunk.method_name or "",
                        source_code=chunk.source_code,
                        vector=vector,
                    )
                )

        return embeddings

    def _process_sequentially(self, chunks: list[CodeChunk]) -> list[Embedding]:
        """Sequential fallback — one embed() call per chunk."""
        embeddings: list[Embedding] = []
        for chunk in chunks:
            embedding = self.generate(chunk)
            embeddings.append(embedding)
        return embeddings