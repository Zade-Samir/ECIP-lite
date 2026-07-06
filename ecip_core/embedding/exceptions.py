class EmbeddingError(Exception):
    """Base exception for all embedding-related errors."""
    pass


class ProviderUnavailableError(EmbeddingError):
    """Raised when the embedding provider is unreachable or down."""
    pass


class EmbeddingTimeoutError(EmbeddingError):
    """Raised when a request to the embedding provider times out."""
    pass


class InvalidVectorError(EmbeddingError):
    """Raised when the embedding provider returns an invalid vector or dimension mismatch."""
    pass
