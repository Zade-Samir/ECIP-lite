import unittest
from ecip_core.retrieval.context.context_builder import ContextBuilder
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.retrieval.context.models.context import Context


class TestContextBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = ContextBuilder()

    def test_empty_context_handling(self):
        ctx = self.builder.build(question="explain UserService", retrieved_results=[])
        self.assertIsInstance(ctx, Context)
        self.assertEqual(ctx.class_context, "")
        self.assertEqual(ctx.method_context, "")
        self.assertEqual(ctx.token_estimate, 0)
        self.assertEqual(ctx.citations, [])

    def test_context_grouping_and_duplicate_removal(self):
        chunks = [
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_1",
                file_path="/src/UserService.java",
                class_name="UserService",
                method_name="",
                chunk_type="class",
                content="public class UserService { private final UserRepository repository; }",
                start_line=1,
                end_line=20
            ),
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_1",
                file_path="/src/UserService.java",
                class_name="UserService",
                method_name="",
                chunk_type="class",
                content="public class UserService { private final UserRepository repository; }",
                start_line=1,
                end_line=20
            ),
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_2",
                file_path="/src/UserService.java",
                class_name="UserService",
                method_name="getUser",
                chunk_type="method",
                content="public User getUser() { return null; }",
                start_line=25,
                end_line=30
            )
        ]

        with self.assertLogs("ecip_core.retrieval.context.context_builder", level="INFO") as log_capture:
            ctx = self.builder.build(question="explain UserService", retrieved_results=chunks)
            self.assertTrue(any("Chunks merged: 1" in log for log in log_capture.output))

        self.assertIn("Class: UserService", ctx.class_context)
        self.assertIn("UserRepository", ctx.dependency_context)
        self.assertIn("getUser", ctx.method_context)
        self.assertEqual(len(ctx.citations), 2)
        self.assertGreater(ctx.token_estimate, 0)

    def test_dependency_extraction_autowired_and_constructor(self):
        class_content_autowired = """
        public class BookingService {
            @Autowired
            private PaymentService paymentService;
        }
        """
        chunks_autowired = [
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_1",
                file_path="/src/BookingService.java",
                class_name="BookingService",
                method_name="",
                chunk_type="class",
                content=class_content_autowired,
                start_line=1,
                end_line=10
            )
        ]
        ctx = self.builder.build(question="how does BookingService work?", retrieved_results=chunks_autowired)
        self.assertIn("Autowired: PaymentService", ctx.dependency_context)

        class_content_constructor = """
        public class OrderService {
            public OrderService(InventoryService inventoryService, CouponService couponService) {}
        }
        """
        chunks_constructor = [
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_2",
                file_path="/src/OrderService.java",
                class_name="OrderService",
                method_name="",
                chunk_type="class",
                content=class_content_constructor,
                start_line=1,
                end_line=10
            )
        ]
        ctx_cons = self.builder.build(question="OrderService dependencies", retrieved_results=chunks_constructor)
        self.assertIn("Constructor Injected: InventoryService", ctx_cons.dependency_context)
        self.assertIn("Constructor Injected: CouponService", ctx_cons.dependency_context)

    def test_warnings_logged_for_missing_information(self):
        chunks = [
            HybridResult(
                source="metadata",
                score=1.0,
                chunk_id="chunk_method",
                file_path="/src/UserService.java",
                class_name="UserService",
                method_name="getUser",
                chunk_type="method",
                content="public User getUser() {}",
                start_line=1,
                end_line=5
            )
        ]
        with self.assertLogs("ecip_core.retrieval.context.context_builder", level="WARNING") as log_capture:
            ctx = self.builder.build(question="getUser method", retrieved_results=chunks)
            self.assertTrue(any("Missing class overview for class: UserService" in log for log in log_capture.output))
            self.assertTrue(any("Missing dependency information for class: UserService" in log for log in log_capture.output))

    def test_serialization(self):
        chunks = [
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
        ctx = self.builder.build(question="explain UserService", retrieved_results=chunks)
        dumped = ctx.model_dump()
        self.assertEqual(dumped["project_name"], "ecip-project")
        self.assertEqual(dumped["question"], "explain UserService")
        self.assertEqual(len(dumped["citations"]), 1)


if __name__ == "__main__":
    unittest.main()
