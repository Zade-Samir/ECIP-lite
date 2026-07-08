import re
from ecip_core.common.logger import get_logger
from ecip_core.retrieval.metadata.metadata_service import MetadataSearchService
from ecip_core.retrieval.semantic_search import SemanticSearch
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.query.entity_extractor import EntityExtractor

logger = get_logger(__name__)


class HybridRetrieval:
    """
    Combines exact metadata queries (from SQLite) with semantic searches (from FAISS).
    Prioritizes deterministic metadata matches over vector similarity.
    """

    def __init__(
        self,
        metadata_service: MetadataSearchService,
        semantic_search: SemanticSearch,
    ):
        self.metadata_service = metadata_service
        self.semantic_search = semantic_search

    def retrieve(self, query: str, k: int = 5) -> list[HybridResult]:
        """
        Retrieves matching code chunks using a hybrid approach:
        Deterministic metadata matches rank first, followed by semantic vector results.
        """
        if not query or not query.strip():
            logger.info("Hybrid query empty, returning empty list.")
            return []

        logger.info(f"Retrieval started for query: {query}")

        # 1. Extract potential entity candidates from query
        class_candidates = set()
        method_candidates = set()
        package_candidates = set()
        file_candidates = set()

        # Run EntityExtractor
        try:
            extractor = EntityExtractor()
            class_name = extractor.extract_class_name(query)
            if class_name:
                class_candidates.add(class_name)
            method_name = extractor.extract_method_name(query)
            if method_name:
                method_candidates.add(method_name)
        except Exception as e:
            logger.warning(f"EntityExtractor failed: {e}")

        # Regex fallback for dotted packages, files, uppercase classes, lowercase methods
        tokens = re.findall(r"\b[A-Za-z0-9_\-\./\\]+\b", query)
        ignore_words = {
            "explain", "show", "list", "find", "where", "what", "which", "give", "get",
            "display", "how", "why", "when", "the", "a", "an", "is", "are", "in", "on", "at",
            "from", "to", "for", "with", "by", "about", "and", "or", "but"
        }
        for token in tokens:
            token_lower = token.lower()
            if token_lower in ignore_words:
                continue

            # Packages (e.g. com.example.auth)
            if "." in token and re.match(r"^[a-z0-9]+(?:\.[a-z0-9]+)+$", token):
                package_candidates.add(token)
                continue

            # Files
            if token.endswith(".java") or "/" in token or "\\" in token:
                file_candidates.add(token)
                continue

            # Classes (CamelCase)
            if re.match(r"^[A-Z][A-Za-z0-9_]*$", token):
                class_candidates.add(token)
                continue

            # Methods (camelCase starting lowercase)
            if re.match(r"^[a-z][A-Za-z0-9_]*$", token):
                method_candidates.add(token)

        # 2. Invoke Metadata Search categorized by Tiers
        # Tier 1: Method matches
        # Tier 2: Class matches
        # Tier 3: Package & File Path matches
        metadata_hits = {}  # key -> (result, tier)

        def add_metadata_hit(res, tier):
            key = (res.file_path, res.class_name, res.method_name, res.start_line, res.end_line)
            if key not in metadata_hits or tier < metadata_hits[key][1]:
                metadata_hits[key] = (res, tier)

        # Retrieve exact methods
        for m in method_candidates:
            try:
                hits = self.metadata_service.search_methods(m, exact=True)
                for h in hits:
                    add_metadata_hit(h, tier=1)
            except Exception as e:
                logger.error(f"Metadata search failure (methods): {e}")

        # Retrieve exact classes
        for c in class_candidates:
            try:
                hits = self.metadata_service.search_classes(c, exact=True)
                for h in hits:
                    add_metadata_hit(h, tier=2)
            except Exception as e:
                logger.error(f"Metadata search failure (classes): {e}")

        # Retrieve exact packages
        for p in package_candidates:
            try:
                hits = self.metadata_service.search_packages(p, exact=True)
                for h in hits:
                    add_metadata_hit(h, tier=3)
            except Exception as e:
                logger.error(f"Metadata search failure (packages): {e}")

        # Retrieve exact file paths
        for f in file_candidates:
            try:
                hits = self.metadata_service.search_file_paths(f, exact=True)
                for h in hits:
                    add_metadata_hit(h, tier=3)
            except Exception as e:
                logger.error(f"Metadata search failure (file paths): {e}")

        logger.info(f"Metadata hits: {len(metadata_hits)}")

        # 3. Invoke Semantic Search
        semantic_hits = []
        try:
            semantic_hits = self.semantic_search.search(query, k=k)
        except Exception as e:
            logger.error(f"Semantic search failure: {e}")

        logger.info(f"Semantic hits: {len(semantic_hits)}")

        # 4. Merge and Deduplicate Results
        merged_candidates = {}

        # First, add metadata matches (they always win and deduplicate)
        for key, (h, tier) in metadata_hits.items():
            score = 1.0 if tier == 1 else (0.9 if tier == 2 else 0.8)
            merged_candidates[key] = (
                HybridResult(
                    source="metadata",
                    score=score,
                    chunk_id=h.chunk_id or f"{h.class_name}_{h.method_name or 'class'}",
                    file_path=h.file_path,
                    class_name=h.class_name,
                    method_name=h.method_name,
                    chunk_type="METHOD" if h.method_name else "CLASS_OVERVIEW",
                    content=h.source_reference,
                    start_line=h.start_line,
                    end_line=h.end_line
                ),
                tier
            )

        # Next, add semantic matches if they aren't already matched by metadata
        for s in semantic_hits:
            key = (s.file_path, s.class_name, s.method_name, s.start_line, s.end_line)
            if key not in merged_candidates:
                merged_candidates[key] = (
                    HybridResult(
                        source="semantic",
                        score=s.score,
                        chunk_id=s.chunk_id,
                        file_path=s.file_path,
                        class_name=s.class_name,
                        method_name=s.method_name,
                        chunk_type=s.chunk_type,
                        content=s.content,
                        start_line=s.start_line,
                        end_line=s.end_line
                    ),
                    4  # Tier 4: Semantic tier
                )

        # 5. Apply ranking rules
        # Priority: Tier 1 (Method exact) > Tier 2 (Class exact) > Tier 3 (Pkg/File exact) > Tier 4 (Semantic)
        # Ties within a tier are broken by score (descending) and chunk_id (alphabetical)
        final_list = list(merged_candidates.values())
        final_list.sort(key=lambda x: (x[1], -x[0].score, x[0].chunk_id))

        results = [item[0] for item in final_list]

        logger.info(f"Final ranked results: {len(results)}")

        if not results:
            logger.warning("No metadata match")
            logger.warning("No semantic match")

        return results
