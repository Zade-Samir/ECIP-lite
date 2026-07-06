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