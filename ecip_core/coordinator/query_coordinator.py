from ecip_core.models.request import InferenceRequest

from ecip_core.inference.inference_service import InferenceService

from ecip_core.query.intent import QueryIntent
from ecip_core.query.intent_analyzer import IntentAnalyzer
from ecip_core.query.entity_extractor import EntityExtractor

from ecip_core.retrieval.metadata.metadata_service import MetadataService
from ecip_core.retrieval.context.context_builder import ContextBuilder


class QueryCoordinator:
    """
    Decides how each developer query should be processed.
    """

    def __init__(self):

        self.intent_analyzer = IntentAnalyzer()
        self.entity_extractor = EntityExtractor()

        self.metadata_service = MetadataService()
        self.context_builder = ContextBuilder()

        self.inference = InferenceService()

    def process(self, request: InferenceRequest):

        question = request.question

        intent = self.intent_analyzer.detect(question)

        # -------------------------
        # Metadata Queries
        # -------------------------

        if intent == QueryIntent.LIST_FILES:

            return self.metadata_service.get_all_files()

        elif intent == QueryIntent.FIND_CLASS:

            class_name = self.entity_extractor.extract_class_name(question)

            return self.metadata_service.get_class(class_name)

        elif intent == QueryIntent.FIND_METHODS:

            class_name = self.entity_extractor.extract_class_name(question)

            return self.metadata_service.get_methods(class_name)

        elif intent == QueryIntent.FIND_FILE_BY_METHOD:

            method_name = self.entity_extractor.extract_method_name(question)

            return self.metadata_service.get_file_by_method(method_name)

        # -------------------------
        # LLM Queries
        # -------------------------

        context = self.context_builder.build(question)

        return self.inference.ask(
            request=request,
            context=context
        )