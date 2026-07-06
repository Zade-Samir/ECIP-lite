import math
import time
from ollama import embed
from ecip_core.embedding.embedding_provider import EmbeddingProvider
from ecip_core.embedding.exceptions import (
    ProviderUnavailableError,
    EmbeddingTimeoutError,
    EmbeddingError,
    InvalidVectorError,
)
from ecip_core.inference.config.settings import settings
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Ollama-based embedding provider implementation.
    Supports both single-item and native batch embedding.
    """

    def __init__(self):
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        logger.info("Provider initialized")

    # ------------------------------------------------------------------
    # Single-item embedding
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        if not text:
            return []

        start_time = time.perf_counter()
        try:
            response = embed(model=self.model, input=text)
        except (ConnectionRefusedError, ConnectionError) as e:
            logger.error("Provider unavailable")
            raise ProviderUnavailableError(f"Ollama provider connection refused: {e}")
        except TimeoutError as e:
            logger.error("Timeout")
            raise EmbeddingTimeoutError(f"Ollama request timed out: {e}")
        except Exception as e:
            msg = str(e).lower()
            if "connection" in msg or "refused" in msg or "unreachable" in msg:
                logger.error("Provider unavailable")
                raise ProviderUnavailableError(f"Ollama provider unreachable: {e}")
            elif "timeout" in msg or "timed out" in msg:
                logger.error("Timeout")
                raise EmbeddingTimeoutError(f"Ollama request timed out: {e}")
            else:
                logger.error(f"Ollama embed failure: {e}")
                raise EmbeddingError(f"Ollama embed failed: {e}")

        duration = time.perf_counter() - start_time
        if duration > 5.0:
            logger.warning("Slow provider")

        if "embeddings" not in response or not response["embeddings"]:
            logger.error("Invalid vector")
            raise InvalidVectorError("Ollama returned response without embeddings.")

        vector = response["embeddings"][0]

        if not self.validate_dimensions(vector):
            logger.error("Invalid vector")
            raise InvalidVectorError(
                f"Generated vector dimension {len(vector)} does not match expected {self.dimension}."
            )

        vector = self.normalize(vector)
        logger.info("Embedding generated")
        return vector

    # ------------------------------------------------------------------
    # Batch embedding
    # ------------------------------------------------------------------

    def supports_batch(self) -> bool:
        return True

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # Filter empty strings but track positions to restore order
        indexed_texts = [(i, t) for i, t in enumerate(texts) if t]
        if not indexed_texts:
            return [[] for _ in texts]

        indices, valid_texts = zip(*indexed_texts)

        start_time = time.perf_counter()
        logger.info(f"Batch started: {len(valid_texts)} items")

        try:
            response = embed(model=self.model, input=list(valid_texts))
        except (ConnectionRefusedError, ConnectionError) as e:
            logger.error("Batch failure")
            raise ProviderUnavailableError(f"Ollama batch connection refused: {e}")
        except TimeoutError as e:
            logger.error("Provider timeout")
            raise EmbeddingTimeoutError(f"Ollama batch timed out: {e}")
        except Exception as e:
            msg = str(e).lower()
            if "connection" in msg or "refused" in msg or "unreachable" in msg:
                logger.error("Batch failure")
                raise ProviderUnavailableError(f"Ollama batch unreachable: {e}")
            elif "timeout" in msg or "timed out" in msg:
                logger.error("Provider timeout")
                raise EmbeddingTimeoutError(f"Ollama batch timed out: {e}")
            else:
                logger.error(f"Batch failure: {e}")
                raise EmbeddingError(f"Ollama batch failed: {e}")

        duration = time.perf_counter() - start_time
        if duration > 5.0:
            logger.warning("Slow provider")

        raw_vectors = response.get("embeddings", [])

        if len(raw_vectors) != len(valid_texts):
            logger.error(f"Invalid vector count: expected {len(valid_texts)}, got {len(raw_vectors)}")
            raise InvalidVectorError(
                f"Ollama returned {len(raw_vectors)} vectors for {len(valid_texts)} inputs."
            )

        # Validate and normalize each returned vector
        validated: list[list[float]] = []
        for i, vector in enumerate(raw_vectors):
            if not self.validate_dimensions(vector):
                logger.error("Invalid vector")
                raise InvalidVectorError(
                    f"Batch item {i}: dimension {len(vector)} != expected {self.dimension}."
                )
            validated.append(self.normalize(vector))

        # Reconstruct output list preserving original order (empty strings → [])
        result: list[list[float]] = [[] for _ in texts]
        for out_idx, orig_idx in enumerate(indices):
            result[orig_idx] = validated[out_idx]

        logger.info(f"Batch completed: {len(validated)} embeddings in {duration:.4f}s")
        return result

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    def validate_dimensions(self, vector: list[float]) -> bool:
        return len(vector) == self.dimension

    def normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return vector
        return [x / norm for x in vector]

    def get_metadata(self) -> dict:
        return {
            "provider": "ollama",
            "model": self.model,
            "dimension": self.dimension,
            "supports_batch": self.supports_batch(),
        }