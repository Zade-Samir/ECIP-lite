import unittest
from unittest.mock import patch, MagicMock
from ecip_core.coordinator.query_coordinator import QueryCoordinator
from ecip_core.models.request import InferenceRequest
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.query.models.entity_result import EntityResult
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.models.response import InferenceResponse
from ecip_core.dependency.models.impact_report import ImpactReport
from ecip_core.dependency.models.relationship import Relationship


class TestQueryCoordinator(unittest.TestCase):

    @patch("ecip_core.coordinator.query_coordinator.InferenceService")
    @patch("ecip_core.coordinator.query_coordinator.ContextBuilder")
    @patch("ecip_core.coordinator.query_coordinator.HybridRetrieval")
    @patch("ecip_core.coordinator.query_coordinator.EntityExtractor")
    @patch("ecip_core.coordinator.query_coordinator.IntentAnalyzer")
    @patch("ecip_core.coordinator.query_coordinator.FAISSStore")
    @patch("ecip_core.coordinator.query_coordinator.EmbeddingService")
    @patch("ecip_core.coordinator.query_coordinator.JavaRepository")
    def setUp(
        self,
        mock_repo,
        mock_embedding,
        mock_faiss,
        mock_intent_class,
        mock_extractor_class,
        mock_retrieval_class,
        mock_context_class,
        mock_inference_class
    ):
        self.mock_intent = mock_intent_class.return_value
        self.mock_extractor = mock_extractor_class.return_value
        self.mock_retrieval = mock_retrieval_class.return_value
        self.mock_context = mock_context_class.return_value
        self.mock_inference = mock_inference_class.return_value

        self.coordinator = QueryCoordinator()

    def test_pipeline_execution_order_and_orchestration(self):
        self.mock_intent.analyze.return_value = IntentResult(
            intent="explain_code",
            confidence=1.0,
            matched_patterns=["explain"],
            normalized_query="explain userservice"
        )
        self.mock_extractor.extract_entities.return_value = [
            EntityResult(
                entity_type="service_name",
                entity_name="UserService",
                confidence=1.0,
                matched_text="UserService",
                normalized_value="userservice"
            )
        ]
        self.mock_retrieval.retrieve.return_value = [
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_1",
                file_path="/src/UserService.java",
                class_name="UserService",
                method_name="",
                chunk_type="class",
                content="public class UserService {}",
                start_line=1,
                end_line=20
            )
        ]
        self.mock_context.build.return_value = "Project context mock"
        self.mock_inference.ask.return_value = InferenceResponse(
            answer="This is UserService overview.",
            model="test-model"
        )

        req = InferenceRequest(question="explain UserService")
        res = self.coordinator.process(req)

        self.assertEqual(res.answer, "This is UserService overview.")
        self.assertEqual(res.model, "test-model")
        self.assertEqual(res.intent.intent, "explain_code")
        self.assertEqual(len(res.entities), 1)
        self.assertEqual(res.entities[0].entity_name, "UserService")
        self.assertEqual(len(res.citations), 1)
        self.assertEqual(res.citations[0].chunk_id, "chunk_1")

        self.mock_intent.analyze.assert_called_once_with("explain UserService")
        self.mock_extractor.extract_entities.assert_called_once_with("explain UserService")
        self.mock_retrieval.retrieve.assert_called_once_with("explain UserService")
        self.mock_context.build.assert_called_once_with("explain UserService")
        self.mock_inference.ask.assert_called_once_with(req, context="Project context mock")

    def test_empty_query_handling(self):
        req = InferenceRequest(question="")
        res = self.coordinator.process(req)

        self.assertEqual(res.answer, "")
        self.assertEqual(res.citations, [])
        self.assertEqual(res.entities, [])
        self.mock_intent.analyze.assert_not_called()

    def test_low_confidence_and_empty_retrieval_logging(self):
        self.mock_intent.analyze.return_value = IntentResult(
            intent="unknown", confidence=0.0, matched_patterns=[], normalized_query="blah"
        )
        self.mock_extractor.extract_entities.return_value = []
        self.mock_context.build.return_value = ""

        # Case A: Empty retrieval
        self.mock_retrieval.retrieve.return_value = []
        self.mock_inference.ask.return_value = InferenceResponse(
            answer="Fallback answer.", model="test-model"
        )

        with self.assertLogs("ecip_core.coordinator.query_coordinator", level="WARNING") as log_capture_empty:
            self.coordinator.process(InferenceRequest(question="blah"))
            self.assertTrue(any("Empty retrieval result" in log for log in log_capture_empty.output))

        # Case B: Low-confidence retrieval
        self.mock_retrieval.retrieve.return_value = [
            HybridResult(
                source="semantic",
                score=0.2,
                chunk_id="chunk_low",
                file_path="/src/Code.java",
                class_name="Code",
                method_name="",
                chunk_type="class",
                content="some content",
                start_line=1,
                end_line=5
            )
        ]
        with self.assertLogs("ecip_core.coordinator.query_coordinator", level="WARNING") as log_capture_low:
            self.coordinator.process(InferenceRequest(question="blah"))
            self.assertTrue(any("Low-confidence retrieval" in log for log in log_capture_low.output))

    def test_error_propagation_service_failure(self):
        self.mock_intent.analyze.side_effect = Exception("Analyzer crashed")

        with self.assertLogs("ecip_core.coordinator.query_coordinator", level="ERROR") as log_capture:
            with self.assertRaises(Exception) as ctx:
                self.coordinator.process(InferenceRequest(question="explain UserService"))
            self.assertIn("Analyzer crashed", str(ctx.exception))
            self.assertTrue(any("Service failure in IntentAnalyzer" in log for log in log_capture.output))

    def test_error_propagation_inference_failure(self):
        self.mock_intent.analyze.return_value = IntentResult(
            intent="explain_code", confidence=1.0, matched_patterns=[], normalized_query="blah"
        )
        self.mock_extractor.extract_entities.return_value = []
        self.mock_retrieval.retrieve.return_value = []
        self.mock_context.build.return_value = ""
        self.mock_inference.ask.side_effect = Exception("Ollama timed out")

        with self.assertLogs("ecip_core.coordinator.query_coordinator", level="ERROR") as log_capture:
            with self.assertRaises(Exception) as ctx:
                self.coordinator.process(InferenceRequest(question="explain UserService"))
            self.assertIn("Ollama timed out", str(ctx.exception))
            self.assertTrue(any("Inference failure" in log for log in log_capture.output))

    def test_response_serialization(self):
        self.mock_intent.analyze.return_value = IntentResult(
            intent="explain_code", confidence=1.0, matched_patterns=[], normalized_query="blah"
        )
        self.mock_extractor.extract_entities.return_value = []
        self.mock_retrieval.retrieve.return_value = []
        self.mock_context.build.return_value = ""
        self.mock_inference.ask.return_value = InferenceResponse(
            answer="Serialized.", model="test-model"
        )

        res = self.coordinator.process(InferenceRequest(question="explain UserService"))
        dumped = res.model_dump()
        self.assertEqual(dumped["answer"], "Serialized.")
        self.assertEqual(dumped["intent"]["intent"], "explain_code")
        self.assertEqual(dumped["entities"], [])
        self.assertEqual(dumped["citations"], [])


    def test_dependency_route_uses_graph_service(self):
        """dependency_analysis intent should call DependencyQueryService, not HybridRetrieval."""
        self.mock_intent.analyze.return_value = IntentResult(
            intent="dependency_analysis",
            confidence=0.9,
            matched_patterns=["depends on"],
            normalized_query="what depends on userrepository"
        )
        self.mock_extractor.extract_entities.return_value = [
            EntityResult(
                entity_type="class_name",
                entity_name="UserRepository",
                confidence=1.0,
                matched_text="UserRepository",
                normalized_value="userrepository"
            )
        ]
        self.mock_inference.ask.return_value = InferenceResponse(
            answer="UserService depends on UserRepository.",
            model="test-model"
        )

        mock_dep_svc = MagicMock()
        mock_dep_svc.get_relationships.return_value = [
            Relationship(
                source_class="UserService",
                target_class="UserRepository",
                relationship_type="DEPENDS_ON",
                depth=1,
                project_id="test-proj"
            )
        ]
        self.coordinator.dependency_service = mock_dep_svc

        req = InferenceRequest(question="What depends on UserRepository?")
        res = self.coordinator.process(req)

        # Graph service must be called, retrieval must NOT be called
        mock_dep_svc.get_relationships.assert_called_once()
        self.mock_retrieval.retrieve.assert_not_called()
        self.assertEqual(res.intent.intent, "dependency_analysis")
        self.assertEqual(res.citations, [])

    def test_impact_route_uses_impact_engine(self):
        """impact_analysis intent should call ImpactAnalysisEngine, not HybridRetrieval."""
        self.mock_intent.analyze.return_value = IntentResult(
            intent="impact_analysis",
            confidence=0.9,
            matched_patterns=["what breaks"],
            normalized_query="what breaks if userservice changes"
        )
        self.mock_extractor.extract_entities.return_value = [
            EntityResult(
                entity_type="class_name",
                entity_name="UserService",
                confidence=1.0,
                matched_text="UserService",
                normalized_value="userservice"
            )
        ]
        self.mock_inference.ask.return_value = InferenceResponse(
            answer="UserController will be affected.",
            model="test-model"
        )

        mock_engine = MagicMock()
        mock_engine.analyze.return_value = ImpactReport(
            project_id="test-proj",
            target_class="UserService",
            affected_classes=["UserController"],
            dependency_tree=[],
            traversal_depth=3,
            total_affected=1,
            warnings=[]
        )
        self.coordinator.impact_engine = mock_engine

        req = InferenceRequest(question="What breaks if UserService changes?")
        res = self.coordinator.process(req)

        mock_engine.analyze.assert_called_once()
        self.mock_retrieval.retrieve.assert_not_called()
        self.assertEqual(res.intent.intent, "impact_analysis")
        self.assertEqual(res.citations, [])

    def test_retrieval_route_for_code_explanation(self):
        """explain_code intent must use hybrid retrieval, not graph."""
        self.mock_intent.analyze.return_value = IntentResult(
            intent="explain_code",
            confidence=0.9,
            matched_patterns=["explain"],
            normalized_query="explain userservice"
        )
        self.mock_extractor.extract_entities.return_value = []
        self.mock_retrieval.retrieve.return_value = [
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_1",
                file_path="/src/UserService.java",
                class_name="UserService",
                method_name="",
                chunk_type="class",
                content="public class UserService {}",
                start_line=1,
                end_line=10
            )
        ]
        self.mock_context.build.return_value = "Context here"
        self.mock_inference.ask.return_value = InferenceResponse(
            answer="UserService is a service.", model="test-model"
        )

        req = InferenceRequest(question="Explain UserService")
        res = self.coordinator.process(req)

        # Retrieval must be called, graph services must NOT be called
        self.mock_retrieval.retrieve.assert_called_once()
        self.assertEqual(res.intent.intent, "explain_code")
        self.assertEqual(len(res.citations), 1)


if __name__ == "__main__":
    unittest.main()
