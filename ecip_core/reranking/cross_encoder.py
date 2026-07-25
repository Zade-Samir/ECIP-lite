import time
import math
from typing import List, Dict, Any, Optional

from ecip_core.common.logger import get_logger
from ecip_core.config.loader import settings
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.reranking.interface import ReRanker

logger = get_logger(__name__)


class CrossEncoderReRanker(ReRanker):
    """
    Cross-Encoder Re-ranker that evaluates query-candidate pairs together
    to produce highly precise semantic relevance scores.
    """

    def __init__(self, model_name: Optional[str] = None):
        cfg = settings.reranking
        self.model_name = model_name or cfg.model_name
        self.batch_size = cfg.batch_size
        self.max_candidates = cfg.max_candidates
        self.top_k = cfg.top_k
        self.device = cfg.device
        self.enable_reranking = cfg.enable_reranking

        self.model = None
        if self.enable_reranking:
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(self.model_name, device=self.device)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error("Model loading failed")
                logger.warning(f"Could not load cross-encoder model '{self.model_name}': {e}. Falling back to token-relevance scoring.")
                self.model = None

    def rerank(self, query: str, candidates: List[HybridResult]) -> List[HybridResult]:
        """
        Scores query-candidate pairs using Cross-Encoder and filters to top_k.
        """
        if not self.enable_reranking:
            logger.warning("Re-ranking disabled")
            return candidates

        if not candidates:
            return []

        if len(candidates) < 2:
            logger.warning("Candidate count below threshold")
            return candidates

        logger.info("Re-ranking started")

        # Trim candidates to max limit to save computation time
        candidates_to_process = candidates[:self.max_candidates]

        # 1. Build query-doc pairs for batch inference
        pairs = []
        for c in candidates_to_process:
            content = c.content or ""
            pairs.append((query, content))

        scores = []
        
        # 2. Batch Inference
        num_batches = math.ceil(len(pairs) / self.batch_size)
        try:
            for b in range(num_batches):
                start = b * self.batch_size
                end = min(start + self.batch_size, len(pairs))
                batch_pairs = pairs[start:end]

                if self.model is not None:
                    # Run inference using sentence_transformers CrossEncoder
                    batch_scores = self.model.predict(batch_pairs)
                    scores.extend([float(s) for s in batch_scores])
                else:
                    # Run fallback token similarity score
                    batch_scores = []
                    for q, doc in batch_pairs:
                        cand = candidates_to_process[len(scores) + len(batch_scores)]
                        score = self._fallback_score(q, doc, cand.class_name, cand.method_name)
                        batch_scores.append(score)
                    scores.extend(batch_scores)

                logger.info("Batch processed")
        except Exception as e:
            logger.error("Inference failed")
            raise RuntimeError(f"Re-ranking inference failed: {e}")

        # 3. Score Normalization
        if len(scores) != len(candidates_to_process):
            logger.error("Invalid scores")
            raise ValueError("Cross-encoder output length mismatch.")

        min_score = min(scores)
        max_score = max(scores)
        rng = max_score - min_score

        normalized_scores = []
        for s in scores:
            if rng == 0.0:
                normalized_scores.append(1.0)
            else:
                normalized_scores.append((s - min_score) / rng)

        # 4. Map normalized scores back to candidates
        for idx, score in enumerate(normalized_scores):
            candidates_to_process[idx].score = score

        # 5. Deterministic sorting: sort by score descending, then chunk_id alphabetically
        re_ranked = sorted(
            candidates_to_process,
            key=lambda x: (-x.score, x.chunk_id)
        )

        results = re_ranked[:self.top_k]
        logger.info("Top-K generated")
        return results

    def _fallback_score(self, query: str, doc_content: str, doc_class: str, doc_method: str) -> float:
        """
        Lightweight fallback lexical similarity heuristic when PyTorch/Transformers are missing.
        """
        from ecip_core.search.bm25.bm25 import tokenize
        q_tokens = tokenize(query)
        doc_tokens = set(tokenize(doc_content))
        
        if not q_tokens:
            return 0.0
            
        matched = 0
        for t in q_tokens:
            if t in doc_tokens:
                matched += 1
                
        score = matched / len(q_tokens)
        
        class_tokens = tokenize(doc_class or "")
        method_tokens = tokenize(doc_method or "")
        for t in q_tokens:
            if t in class_tokens:
                score += 0.2
            if t in method_tokens:
                score += 0.3
                
        return min(1.0, max(0.0, score))
