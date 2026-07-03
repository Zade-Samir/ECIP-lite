from abc import ABC, abstractmethod

from ecip_core.chunking.code_chunk import CodeChunk
from ecip_core.embedding.models.embedding import Embedding


class EmbeddingProvider(ABC):
    """
    Base interface for embedding providers.
    """

    @abstractmethod

    def embed(
        self,
        text: str
    ) -> list[float]:
        pass