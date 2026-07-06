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
    """

    def __init__(self):
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        logger.info("Provider initialized")

    def embed(self, text: str) -> list[float]:
        if not text:
            return []

        start_time = time.perf_counter()
        try:
            response = embed(
                model=self.model,
                input=text
            )
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
            logger.warning("Slow embedding request")

        if "embeddings" not in response or not response["embeddings"]:
            logger.error("Invalid vector")
            raise InvalidVectorError("Ollama returned response without embeddings.")

        vector = response["embeddings"][0]
        
        # Validation and normalization responsibilities of provider
        if not self.validate_dimensions(vector):
            logger.error("Invalid vector")
            raise InvalidVectorError(
                f"Generated vector dimension {len(vector)} does not match expected {self.dimension}."
            )

        vector = self.normalize(vector)

        logger.info("Embedding generated")
        logger.info(f"Vector dimension: {len(vector)}")
        return vector

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
            "dimension": self.dimension
        }