from abc import ABC, abstractmethod
from typing import List
from ecip_core.retrieval.models.hybrid_result import HybridResult


class ReRanker(ABC):
    """
    Abstract Base Class defining the contract for result re-rankers.
    """

    @abstractmethod
    def rerank(self, query: str, candidates: List[HybridResult]) -> List[HybridResult]:
        """
        Re-scores and re-ranks retrieved candidates against the query.
        """
        pass
