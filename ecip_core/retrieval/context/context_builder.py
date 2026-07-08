import re
from ecip_core.common.logger import get_logger
from ecip_core.query.entity_extractor import EntityExtractor
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.retrieval.context.models.context import Context

logger = get_logger(__name__)


class ContextBuilder:
    """
    Builds project context for the LLM using project metadata and hybrid retrieval.
    """

    def __init__(self):
        self.repository = JavaRepository()
        self.extractor = EntityExtractor()

    def build(
        self,
        question: str,
        retrieved_results: list[HybridResult] = None,
        project_id: str = "default",
        project_name: str = "ecip-project"
    ) -> Context | str:
        """
        Builds structured context. Returns Context object if retrieved_results is provided,
        otherwise fallback to legacy string mode.
        """
        # Legacy fallback mode
        if retrieved_results is None:
            class_name = self.extractor.extract_class_name(question)
            if class_name is None:
                return ""
            java_class = self.repository.find_by_class_name(class_name)
            if java_class is None:
                return ""
            methods = self.repository.find_methods(class_name)
            return f"""Project Context

Class:
{java_class["class_name"]}

Package:
{java_class["package_name"]}

Methods:
{", ".join(methods)}
"""

        # Hybrid Context Builder Mode
        logger.info("Context generation started")

        if not retrieved_results:
            logger.info("Empty retrieval results, returning empty context")
            return Context(
                project_id=project_id,
                project_name=project_name,
                question=question,
                class_context="",
                method_context="",
                dependency_context="",
                supporting_chunks=[],
                citations=[],
                token_estimate=0
            )

        try:
            grouped_chunks = {}
            seen_chunk_ids = set()
            unique_results = []

            for r in retrieved_results:
                if r.chunk_id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(r.chunk_id)
                unique_results.append(r)

                class_key = r.class_name if r.class_name else "UnknownClass"
                if class_key not in grouped_chunks:
                    grouped_chunks[class_key] = []
                grouped_chunks[class_key].append(r)

            merged_count = len(retrieved_results) - len(unique_results)
            logger.info(f"Chunks merged: {merged_count}")

            class_context_parts = []
            method_context_parts = []
            dependency_context_parts = []
            supporting_chunks = []
            citations = []

            for class_name, chunks in grouped_chunks.items():
                class_overview_found = False
                has_deps = False
                class_header = f"Class: {class_name}\n"

                overview_content = []
                for chunk in chunks:
                    if chunk.chunk_type == "class" or chunk.chunk_type == "file":
                        class_overview_found = True
                        overview_content.append(chunk.content)
                        citations.append(chunk)

                        deps = self._extract_dependencies(chunk.content, class_name)
                        if "No constructor dependencies" not in deps:
                            has_deps = True
                            dependency_context_parts.append(f"Dependencies for class {class_name}:\n{deps}\n")

                if class_overview_found:
                    class_context_parts.append(class_header + "\n".join(overview_content) + "\n")
                else:
                    logger.warning(f"Missing class overview for class: {class_name}")

                if not has_deps:
                    logger.warning(f"Missing dependency information for class: {class_name}")

                class_methods = []
                for chunk in chunks:
                    if chunk.chunk_type == "method":
                        class_methods.append(f"Method {chunk.method_name}:\n{chunk.content}\n")
                        citations.append(chunk)
                    elif chunk.chunk_type not in ("class", "file"):
                        supporting_chunks.append(chunk)

                if class_methods:
                    method_context_parts.append(f"Methods of {class_name}:\n" + "\n".join(class_methods))

            class_context = "\n".join(class_context_parts).strip()
            method_context = "\n".join(method_context_parts).strip()
            dependency_context = "\n".join(dependency_context_parts).strip()

            # De-duplicate citations
            citations = list({c.chunk_id: c for c in citations}.values())
            logger.info(f"Citations generated: {len(citations)}")

            # Word heuristic token estimate
            combined_text = (
                f"Project: {project_name}\n"
                f"Question: {question}\n"
                f"Class context:\n{class_context}\n"
                f"Method context:\n{method_context}\n"
                f"Dependency context:\n{dependency_context}\n"
            )
            token_estimate = int(len(combined_text) / 4) + 1
            logger.info(f"Token estimate: {token_estimate}")

            return Context(
                project_id=project_id,
                project_name=project_name,
                question=question,
                class_context=class_context,
                method_context=method_context,
                dependency_context=dependency_context,
                supporting_chunks=supporting_chunks,
                citations=citations,
                token_estimate=token_estimate
            )

        except Exception as e:
            logger.error(f"Context generation failure: {e}")
            raise

    def _extract_dependencies(self, class_content: str, class_name: str) -> str:
        """
        Parses final declarations, @Autowired fields, or constructors to extract dependency class types.
        """
        dependencies = []

        field_matches = re.findall(r"private\s+final\s+([A-Z][a-zA-Z0-9_]*)\s+([a-z][a-zA-Z0-9_]*)\s*;", class_content)
        for type_name, var_name in field_matches:
            dependencies.append(f"- Injected: {type_name} ({var_name})")

        autowired_matches = re.findall(
            r"@Autowired\s+(?:private|protected|public)?\s+([A-Z][a-zA-Z0-9_]*)\s+([a-z][a-zA-Z0-9_]*)\s*;", class_content
        )
        for type_name, var_name in autowired_matches:
            dependencies.append(f"- Autowired: {type_name} ({var_name})")

        constructor_pattern = rf"public\s+{class_name}\s*\(([^)]*)\)"
        constructor_match = re.search(constructor_pattern, class_content)
        if constructor_match:
            params = constructor_match.group(1).strip()
            if params:
                for param in params.split(","):
                    parts = param.strip().split()
                    if len(parts) >= 2:
                        dependencies.append(f"- Constructor Injected: {parts[-2]} ({parts[-1]})")

        unique_deps = list(dict.fromkeys(dependencies))
        if not unique_deps:
            return "No constructor dependencies found."
        return "\n".join(unique_deps)