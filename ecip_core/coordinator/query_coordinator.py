import sys
from ecip_core.common.logger import get_logger
from ecip_core.models.request import InferenceRequest
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.query.models.entity_result import EntityResult
from ecip_core.query.models.coordinator_response import CoordinatorResponse
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.dependency.dependency_service import DependencyQueryService
from ecip_core.dependency.impact_analysis import ImpactAnalysisEngine

# Graph-routed intents: these bypass semantic retrieval
GRAPH_INTENTS = {"dependency_analysis", "impact_analysis"}

# Define compatibility layer for old ContextBuilder imports
from ecip_core.storage.sqlite.repository import JavaRepository

class MetadataServiceCompatibility:
    """
    Compatibility layer to keep the old ContextBuilder functioning without breaking.
    """
    def __init__(self):
        self.repository = JavaRepository()

    def get_all_files(self):
        return self.repository.get_all_files()

    def get_class(self, class_name: str):
        return self.repository.find_by_class_name(class_name)

    def get_methods(self, class_name: str):
        return self.repository.find_methods(class_name)

    def get_file_by_method(self, method_name: str):
        return self.repository.find_file_by_method(method_name)

# Inject compatibility class into metadata_service module before ContextBuilder imports it
from ecip_core.retrieval.metadata import metadata_service
metadata_service.MetadataService = MetadataServiceCompatibility

# Now import retrieval services safely
from ecip_core.retrieval.metadata.metadata_service import MetadataSearchService
from ecip_core.retrieval.semantic_search import SemanticSearch
from ecip_core.retrieval.hybrid_retrieval import HybridRetrieval
from ecip_core.retrieval.context.context_builder import ContextBuilder
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.inference.inference_service import InferenceService
from ecip_core.query.intent_analyzer import IntentAnalyzer
from ecip_core.query.entity_extractor import EntityExtractor
from ecip_core.inference.config.settings import settings

logger = get_logger(__name__)


class QueryCoordinator:
    """
    Central orchestration layer for the entire question-answering pipeline.
    """

    def __init__(self):
        try:
            self.intent_analyzer = IntentAnalyzer()
            self.entity_extractor = EntityExtractor()

            # Initialize search & retrieval
            self.repository = JavaRepository()
            self.faiss_store = FAISSStore(
                index_path=settings.FAISS_INDEX_PATH,
                metadata_path=settings.FAISS_METADATA_PATH
            )
            self.metadata_service = MetadataSearchService(
                repository=self.repository,
                faiss_store=self.faiss_store
            )
            self.embedding_service = EmbeddingService(
                batch_size=settings.EMBEDDING_BATCH_SIZE
            )
            self.semantic_search = SemanticSearch(
                embedding_service=self.embedding_service,
                faiss_store=self.faiss_store
            )
            self.hybrid_retrieval = HybridRetrieval(
                metadata_service=self.metadata_service,
                semantic_search=self.semantic_search
            )

            # Graph analysis services
            self.dependency_service = DependencyQueryService()
            self.impact_engine = ImpactAnalysisEngine()

            # Context & inference
            self.context_builder = ContextBuilder()
            self.inference = InferenceService()

        except Exception as e:
            logger.error(f"Service failure during initialization: {e}")
            raise

    def process(self, request: InferenceRequest) -> CoordinatorResponse:
        """
        Orchestrates intent analysis, entity extraction, hybrid retrieval,
        context building, prompt generation, inference, and citations.
        """
        try:
            # 1. Normalize request
            question = request.question.strip() if request.question else ""
            logger.info("Query received")

            if not question:
                logger.warning("Empty query received")
                return CoordinatorResponse(
                    answer="",
                    model=settings.MODEL_NAME,
                    intent=IntentResult(intent="unknown", confidence=0.0, matched_patterns=[], normalized_query=""),
                    entities=[],
                    citations=[]
                )

            # 2. Invoke Intent Analyzer
            try:
                intent_res = self.intent_analyzer.analyze(question)
                logger.info(f"Intent detected: {intent_res.intent}")
            except Exception as e:
                logger.error(f"Service failure in IntentAnalyzer: {e}")
                raise

            # 3. Invoke Entity Extractor
            try:
                entities = self.entity_extractor.extract_entities(question)
                logger.info(f"Entities extracted: {len(entities)}")
            except Exception as e:
                logger.error(f"Service failure in EntityExtractor: {e}")
                raise

            # 4. Route by intent
            if intent_res.intent in GRAPH_INTENTS:
                # --- GRAPH ROUTE: dependency or impact analysis ---
                logger.info(f"Intent routed: graph ({intent_res.intent})")
                target_class = entities[0].entity_name if entities else ""
                project_id = getattr(request, "project_id", None)

                try:
                    if intent_res.intent == "impact_analysis":
                        report = self.impact_engine.analyze(
                            target_class=target_class,
                            depth=3,
                            project_id=project_id
                        )
                        if report.total_affected == 0:
                            logger.warning("Empty graph result")
                            graph_summary = f"No classes are affected by changes to '{target_class}'."
                        else:
                            lines = [f"Impact analysis for '{target_class}':"]
                            for cls in report.affected_classes:
                                lines.append(f"  - {cls}")
                            graph_summary = "\n".join(lines)
                        logger.info("Graph analysis executed")

                    else:  # dependency_analysis
                        relationships = self.dependency_service.get_relationships(
                            class_name=target_class,
                            project_id=project_id
                        )
                        if not relationships:
                            logger.warning("Empty graph result")
                            graph_summary = f"No dependency relationships found for '{target_class}'."
                        else:
                            lines = [f"Dependency relationships for '{target_class}':"]
                            for rel in relationships:
                                lines.append(
                                    f"  - {rel.source_class} --{rel.relationship_type}--> {rel.target_class}"
                                )
                            graph_summary = "\n".join(lines)
                        logger.info("Graph analysis executed")

                except Exception as e:
                    logger.error(f"Routing failure: {e}")
                    raise

                # Summarize graph facts via LLM
                try:
                    logger.info("Prompt generated")
                    inference_res = self.inference.ask(request, context=graph_summary)
                except Exception as e:
                    logger.error(f"Inference failure: {e}")
                    raise

                response = CoordinatorResponse(
                    answer=inference_res.answer,
                    model=inference_res.model,
                    intent=intent_res,
                    entities=entities,
                    citations=[]
                )
                logger.info("Response returned")
                return response

            else:
                # --- RETRIEVAL ROUTE: code explanation, semantic questions ---
                logger.info("Intent routed: retrieval")

                # Execute Hybrid Retrieval
                try:
                    retrieved_results = self.hybrid_retrieval.retrieve(question)
                    logger.info(f"Retrieval completed: {len(retrieved_results)}")
                except Exception as e:
                    logger.error(f"Service failure in HybridRetrieval: {e}")
                    raise

                if not retrieved_results:
                    logger.warning("Empty retrieval result")
                elif all(r.score < 0.4 for r in retrieved_results if r.source == "semantic"):
                    logger.warning("Low-confidence retrieval")

                # Build Context
                try:
                    context = self.context_builder.build(question)
                    if not context.strip() and retrieved_results:
                        context_parts = ["Project Context:"]
                        for r in retrieved_results:
                            context_parts.append(
                                f"File: {r.file_path}\n"
                                f"Class: {r.class_name}\n"
                                f"Method: {r.method_name}\n"
                                f"Content:\n{r.content}\n"
                            )
                        context = "\n".join(context_parts)
                except Exception as e:
                    logger.error(f"Service failure in ContextBuilder: {e}")
                    raise

                # Execute inference
                try:
                    logger.info("Prompt generated")
                    inference_res = self.inference.ask(request, context=context)
                except Exception as e:
                    logger.error(f"Inference failure: {e}")
                    raise

                response = CoordinatorResponse(
                    answer=inference_res.answer,
                    model=inference_res.model,
                    intent=intent_res,
                    entities=entities,
                    citations=retrieved_results
                )
                logger.info("Response returned")
                return response

        except Exception as e:
            logger.error(f"Unexpected pipeline error: {e}")
            raise