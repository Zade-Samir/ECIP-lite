from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Base interface for embedding providers.
    """

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate embedding vector for the given text.

        Raises:
            ProviderUnavailableError: If the provider is unreachable/offline.
            EmbeddingTimeoutError: If the request times out.
            EmbeddingError: For general embedding operation failures.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embedding vectors for a batch of texts.
        Returned list must preserve the same order as input texts.

        Raises:
            ProviderUnavailableError: If the provider is unreachable/offline.
            EmbeddingTimeoutError: If the request times out.
            InvalidVectorError: If returned vector count doesn't match input count.
            EmbeddingError: For general embedding operation failures.
        """
        pass

    @abstractmethod
    def supports_batch(self) -> bool:
        """
        Return True if the provider natively supports batch embedding requests.
        If False, EmbeddingService will fall back to sequential single-item calls.
        """
        pass

    @abstractmethod
    def validate_dimensions(self, vector: list[float]) -> bool:
        """
        Validate that the generated vector matches the expected dimension.
        """
        pass

    @abstractmethod
    def normalize(self, vector: list[float]) -> list[float]:
        """
        Perform L2 normalization on the embedding vector.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> dict:
        """
        Return metadata of the provider (e.g. model name, dimensions).
        """
        pass