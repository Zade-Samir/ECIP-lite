import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from ecip_core.common.logger import get_logger
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.search.bm25.bm25 import BM25Index
from ecip_core.workspace.manager import workspace_manager

logger = get_logger(__name__)


class HybridRetrievalEngine:
    """
    Hybrid Retrieval Engine combining lexical BM25 keyword matching
    with dense vector semantic similarity scoring.
    """

    def __init__(
        self,
        semantic_search_service,
        bm25_weight: float = 0.40,
        vector_weight: float = 0.60
    ):
        self.semantic_search = semantic_search_service
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self._bm25_cache = {}  # (project_id, mtime) -> BM25Index
        from ecip_core.reranking.cross_encoder import CrossEncoderReRanker
        self.reranker = CrossEncoderReRanker()

    def retrieve(self, query: str, k: int = 5) -> List[HybridResult]:
        """
        Executes BM25 search and vector search, normalizes scores,
        applies weighted rank fusion, removes duplicates, and returns ranked results.
        """
        if not query or not query.strip():
            return []

        logger.info(f"Retrieval started for query: {query}")

        # 1. Fetch active workspace metadata to find paths
        project_id = workspace_manager.get_active_workspace()
        workspace = workspace_manager.get_workspace(project_id)
        if not workspace:
            logger.error("Rank fusion failure")
            raise ValueError(f"Active workspace '{project_id}' is not registered.")

        # 2. Execute BM25 search
        bm25_hits = []
        try:
            bm25_path = Path(workspace["root_path"]) / ".ecip" / "bm25_index.json"
            if bm25_path.exists():
                mtime = bm25_path.stat().st_mtime
                cache_key = (project_id, mtime)
                if cache_key in self._bm25_cache:
                    bm25_index = self._bm25_cache[cache_key]
                else:
                    bm25_index = BM25Index()
                    bm25_index.load(str(bm25_path))
                    self._bm25_cache = {cache_key: bm25_index}

                bm25_hits = bm25_index.search(query, k=k * 2)
                logger.info("BM25 search completed")
            else:
                logger.warning("Missing BM25 index")
        except Exception as e:
            logger.error("BM25 index unavailable")
            logger.error(f"BM25 retrieval failed: {e}")

        # 3. Execute Vector search
        vector_hits = []
        try:
            # semantic_search.search returns list of Embedding/HybridResult objects
            vector_hits = self.semantic_search.search(query, k=k * 2)
            logger.info("Vector search completed")
        except Exception as e:
            logger.error("Semantic retrieval failed")
            logger.error(f"Semantic search failed: {e}")

        if not bm25_hits:
            logger.warning("Empty lexical results")
        if not vector_hits:
            logger.warning("Empty semantic results")

        # 4. Normalize scores
        # Normalization helper
        def get_normalized_scores(hits: list, is_vector: bool) -> Dict[str, float]:
            if not hits:
                return {}
            
            # Extract raw scores
            if is_vector:
                # Semantic search outputs might have distance/similarity score
                raw_scores = [getattr(h, "score", 0.0) for h in hits]
            else:
                raw_scores = [h["score"] for h in hits]

            if not raw_scores:
                return {}

            min_score = min(raw_scores)
            max_score = max(raw_scores)
            rng = max_score - min_score

            norm_map = {}
            for i, h in enumerate(hits):
                cid = getattr(h, "chunk_id", None) or h.get("chunk_id")
                if not cid:
                    continue
                
                # Normalize between 0 and 1
                if rng == 0.0:
                    norm = 1.0
                else:
                    norm = (raw_scores[i] - min_score) / rng
                
                # If vector, L2 distance: smaller is better, so invert it
                if is_vector:
                    norm = 1.0 - norm
                    
                norm_map[cid] = norm
            return norm_map

        norm_bm25 = get_normalized_scores(bm25_hits, is_vector=False)
        norm_vector = get_normalized_scores(vector_hits, is_vector=True)

        # 5. Merge duplicates and apply weighted rank fusion
        merged = {}  # chunk_id -> (fused_score, result_obj)
        
        # Helper to register candidate
        def register_candidate(cid, base_hit, source_name):
            if cid in merged:
                return
            
            # Create a base HybridResult
            if isinstance(base_hit, dict):
                res = HybridResult(
                    source=source_name,
                    score=0.0,
                    chunk_id=cid,
                    file_path=base_hit.get("file_path") or "",
                    class_name=base_hit.get("class_name") or "",
                    method_name=base_hit.get("method_name") or "",
                    chunk_type=base_hit.get("chunk_type") or "CLASS_OVERVIEW",
                    content=base_hit.get("content") or "",
                    start_line=base_hit.get("start_line") or 1,
                    end_line=base_hit.get("end_line") or 1
                )
            else:
                res = HybridResult(
                    source=source_name,
                    score=0.0,
                    chunk_id=cid,
                    file_path=getattr(base_hit, "file_path", None) or "",
                    class_name=getattr(base_hit, "class_name", None) or "",
                    method_name=getattr(base_hit, "method_name", None) or "",
                    chunk_type=getattr(base_hit, "chunk_type", None) or "CLASS_OVERVIEW",
                    content=getattr(base_hit, "content", None) or getattr(base_hit, "source_code", None) or "",
                    start_line=getattr(base_hit, "start_line", None) or 1,
                    end_line=getattr(base_hit, "end_line", None) or 1
                )
            merged[cid] = [0.0, res]

        # Register all candidates
        for h in bm25_hits:
            register_candidate(h["chunk_id"], h, "hybrid")
        for h in vector_hits:
            cid = getattr(h, "chunk_id", None)
            if cid:
                register_candidate(cid, h, "hybrid")

        # Compute fused score for each unique chunk
        for cid, (fused, res) in list(merged.items()):
            score_b = norm_bm25.get(cid, 0.0)
            score_v = norm_vector.get(cid, 0.0)
            
            # Weighted sum
            fused_score = (self.bm25_weight * score_b) + (self.vector_weight * score_v)
            res.score = fused_score
            merged[cid][0] = fused_score

        # 6. Deterministic sorting: sort by score descending, then chunk_id alphabetically
        sorted_candidates = sorted(
            merged.values(),
            key=lambda x: (-x[0], x[1].chunk_id)
        )

        candidates = [item[1] for item in sorted_candidates]
        logger.info("Rank fusion complete")

        # 7. Apply Re-ranking stage
        results = self.reranker.rerank(query, candidates)
        return results[:k]
