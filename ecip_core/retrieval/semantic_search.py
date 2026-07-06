import time
from ecip_core.common.logger import get_logger
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.retrieval.models.search_result import SearchResult

logger = get_logger(__name__)


class SemanticSearch:
    """
    Service responsible for converting queries into embeddings,
    querying FAISS, ranking results, and returning structured typed results.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        faiss_store: FAISSStore,
    ):
        self.embedding_service = embedding_service
        self.faiss_store = faiss_store

    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        """
        Execute semantic search for the given natural language query.
        """
        if not query or not query.strip():
            logger.info("Search with empty query received, returning empty results.")
            return []

        logger.info(f"Query received: {query}")

        start_time = time.perf_counter()
        try:
            query_vector = self.embedding_service.embed_question(query)
        except Exception as e:
            logger.error(f"Embedding failure: {e}")
            raise

        # Validate dimensions
        if len(query_vector) != self.faiss_store.dimension:
            logger.error(
                f"Invalid vector dimensions: expected {self.faiss_store.dimension}, "
                f"got {len(query_vector)}"
            )
            raise ValueError(
                f"Vector dimension mismatch: expected {self.faiss_store.dimension}, "
                f"got {len(query_vector)}."
            )

        logger.info("Embedding generated")

        try:
            matches = self.faiss_store.search_with_scores(query_vector, k)
        except Exception as e:
            logger.error(f"Search failure: {e}")
            raise

        results: list[SearchResult] = []
        for embedding, distance in matches:
            # Map squared L2 distance to score in [0, 1] using cosine similarity formula
            # For normalized vectors, d^2 = 2 * (1 - cos_sim) => cos_sim = 1 - d^2 / 2
            cosine_similarity = 1.0 - (distance / 2.0)
            score = max(0.0, min(1.0, cosine_similarity))

            results.append(
                SearchResult(
                    score=score,
                    chunk_id=embedding.chunk_id or "",
                    file_path=embedding.file_path or "",
                    class_name=embedding.class_name,
                    method_name=embedding.method_name or "",
                    chunk_type=embedding.chunk_type or "METHOD",
                    start_line=embedding.start_line or 0,
                    end_line=embedding.end_line or 0,
                    content=embedding.source_code,
                )
            )

        # Deterministic ordering: primary sort by descending score, secondary by chunk_id
        results.sort(key=lambda x: (-x.score, x.chunk_id))

        duration = time.perf_counter() - start_time
        logger.info(f"Search completed: {len(results)} results in {duration:.4f}s")

        # Logging warnings for confidence
        if not results:
            logger.warning("No semantic matches")
        elif results[0].score < 0.3:
            logger.warning(
                f"Low confidence results: top score is {results[0].score:.4f}"
            )

        return results
