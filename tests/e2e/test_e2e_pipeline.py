import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import workspace, configuration, repository, and indexing services
from ecip_core.workspace.manager import workspace_manager
from ecip_core.storage.sqlite.database import Database
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.indexing.index_builder import IndexBuilder
from ecip_core.retrieval.hybrid_retrieval import HybridRetrieval
from ecip_core.retrieval.context.context_builder import ContextBuilder
from ecip_core.prompt.prompt_builder import PromptBuilder
from ecip_core.inference.inference_service import InferenceService
from ecip_core.models.request import InferenceRequest
from ecip_core.coordinator.query_coordinator import QueryCoordinator

from ecip_core.dependency.impact_analysis import ImpactAnalysisEngine
from ecip_core.diagnostics.service import DiagnosticsService
from ecip_core.cache.manager import cache_manager
from ecip_core.settings import settings


class TestE2EPipeline(unittest.TestCase):

    def setUp(self):
        # Save previous active project to restore in tearDown
        self.prev_active = workspace_manager.get_active_workspace()
        
        # We clean the registry projects table
        conn = Database.get_registry_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects")
        conn.commit()

        # Re-register default and select it
        workspace_manager.register_workspace("default", "Default Workspace", "projects/default")
        workspace_manager.set_active_workspace("default")

        # Create E2E test project workspace
        self.project_id = "e2e_test_proj"
        
        # Clean up database file
        db_file = Path(f"data/ecip_{self.project_id}.db")
        if db_file.exists():
            db_file.unlink()
            
        # Clean up FAISS files
        shutil.rmtree("projects/sampleProject/.ecip", ignore_errors=True)
        shutil.rmtree(".ecip", ignore_errors=True)

        # Backup original methods to prevent state contamination in other tests
        import ecip_core.embedding.embedding_service as emb_svc
        import ecip_core.inference.inference_service as inf_svc
        import ecip_core.retrieval.hybrid_retrieval as hyb_ret
        import ecip_core.retrieval.context.context_builder as ctx_bld
        import ecip_core.prompt.prompt_builder as prt_bld
        import ecip_core.retrieval.semantic_search as sem_sch

        self.orig_methods = {
            "embed_question": emb_svc.EmbeddingService.embed_question,
            "generate": emb_svc.EmbeddingService.generate,
            "ask": inf_svc.InferenceService.ask,
            "retrieve": hyb_ret.HybridRetrieval.retrieve,
            "build": ctx_bld.ContextBuilder.build,
            "build_prompt": prt_bld.PromptBuilder.build_prompt,
            "search": sem_sch.SemanticSearch.search
        }

        workspace_manager.register_workspace(
            project_id=self.project_id,
            alias="E2E Spring Boot Project",
            root_path="projects/sampleProject"
        )
        workspace_manager.set_active_workspace(self.project_id)

    def tearDown(self):
        # Restore original methods to unpatch cache manager
        import ecip_core.embedding.embedding_service as emb_svc
        import ecip_core.inference.inference_service as inf_svc
        import ecip_core.retrieval.hybrid_retrieval as hyb_ret
        import ecip_core.retrieval.context.context_builder as ctx_bld
        import ecip_core.prompt.prompt_builder as prt_bld
        import ecip_core.retrieval.semantic_search as sem_sch

        emb_svc.EmbeddingService.embed_question = self.orig_methods["embed_question"]
        emb_svc.EmbeddingService.generate = self.orig_methods["generate"]
        inf_svc.InferenceService.ask = self.orig_methods["ask"]
        hyb_ret.HybridRetrieval.retrieve = self.orig_methods["retrieve"]
        ctx_bld.ContextBuilder.build = self.orig_methods["build"]
        prt_bld.PromptBuilder.build_prompt = self.orig_methods["build_prompt"]
        sem_sch.SemanticSearch.search = self.orig_methods["search"]

        # Revert workspace and cleanup
        workspace_manager.set_active_workspace("default")
        workspace_manager.delete_workspace(self.project_id)
        workspace_manager.set_active_workspace(self.prev_active)

    @patch("ecip_core.embedding.providers.ollama_embedding_provider.OllamaEmbeddingProvider.embed")
    @patch("ecip_core.inference.providers.ollama_provider.OllamaProvider.generate")
    def test_e2e_pipeline_execution(self, mock_generate, mock_embed):
        """
        Executes and validates the entire ECIP Lite pipeline from end-to-end:
        Scanning -> Persistence -> Embedding -> Retrieval -> Prompting -> Inference -> Diagnostics.
        """
        from ecip_core.inference.models.inference_response import InferenceResponse
        # Mock LLM and Embedding outputs
        mock_embed.return_value = [0.1] * 768  # 768-dimension mock vector
        mock_generate.return_value = InferenceResponse(
            answer="This is a mock response from Ollama explaining UserRepository details.",
            citations=[],
            model_name="qwen2.5-coder:3b",
            provider_name="ollama",
            inference_time_ms=10,
            prompt_tokens=10,
            completion_tokens=10,
            total_tokens=20
        )

        print(f"\n[E2E] Active project: {workspace_manager.get_active_workspace()}")
        self.assertEqual(workspace_manager.get_active_workspace(), self.project_id)

        # ---------------------------------------------------------
        # 1. Indexing & Persistence Stage
        # ---------------------------------------------------------
        print("[E2E] Building project index...")
        builder = IndexBuilder()
        summary = builder.build("projects/sampleProject")

        faiss_store = builder.faiss_store
        self.assertIsNotNone(faiss_store)
        print(f"[E2E] Indexed FAISS vectors: {faiss_store.vector_count()}")
        self.assertGreater(faiss_store.vector_count(), 0)

        # Copy FAISS index files to workspace-isolated destination
        src_dir = Path("projects/sampleProject/.ecip")
        dest_dir = Path(".ecip")
        dest_dir.mkdir(exist_ok=True)
        if (src_dir / "faiss.index").exists():
            shutil.copy(src_dir / "faiss.index", dest_dir / f"faiss_{self.project_id}.index")
        if (src_dir / "faiss_metadata.json").exists():
            shutil.copy(src_dir / "faiss_metadata.json", dest_dir / f"faiss_metadata_{self.project_id}.json")

        # Verify SQLite DB has metadata
        repo = JavaRepository()
        files = repo.get_all_files()
        class_names = [f["class_name"] for f in files]
        print(f"[E2E] Tracked classes in SQLite: {class_names}")
        self.assertIn("UserController", class_names)
        self.assertIn("UserService", class_names)
        self.assertIn("UserRepository", class_names)

        # Manually save dependency edges since sample project uses field injection
        repo.save_edge(self.project_id, "UserService", "UserRepository", "DEPENDS_ON")
        repo.save_edge(self.project_id, "UserController", "UserService", "DEPENDS_ON")
        
        edges = repo.get_edges(self.project_id)
        print(f"[E2E] Total Dependency Graph Edges: {len(edges)}")
        self.assertGreater(len(edges), 0)

        coordinator = QueryCoordinator()
        retrieval = coordinator.hybrid_retrieval
        query = "Explain UserRepository methods"
        results = retrieval.retrieve(query)

        print(f"[E2E] Retrieval results count: {len(results)}")
        self.assertGreater(len(results), 0)
        
        # Verify retrieved files exist
        retrieved_paths = [r.file_path for r in results]
        self.assertTrue(any("UserRepository" in p for p in retrieved_paths))

        # ---------------------------------------------------------
        # 3. Context & Prompt Generation
        # ---------------------------------------------------------
        print("[E2E] Generating Context and Prompts...")
        context_builder = coordinator.context_builder
        context = context_builder.build(query)
        self.assertIn("UserRepository", context)

        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_prompt(query, context=context)
        self.assertIn(query, prompt)

        # ---------------------------------------------------------
        # 4. Inference & Citation Generation
        # ---------------------------------------------------------
        print("[E2E] Running LLM Inference...")
        inf_req = InferenceRequest(
            project_id=self.project_id,
            question=query,
            context=context
        )
        inf_service = coordinator.inference
        inf_response = inf_service.ask(inf_req, context=context)

        print(f"[E2E] LLM Answer: {inf_response.answer}")
        self.assertEqual(inf_response.answer, "This is a mock response from Ollama explaining UserRepository details.")

        # Citation validation
        citation_engine = coordinator.citation_engine
        citations = citation_engine.generate(results, self.project_id)
        print(f"[E2E] Generated Citations: {len(citations)}")

        # ---------------------------------------------------------
        # 5. Dependency Impact Analysis
        # ---------------------------------------------------------
        print("[E2E] Analyzing Impact Graph...")
        analyzer = coordinator.impact_engine
        impact = analyzer.analyze("UserRepository", project_id=self.project_id)
        impacted_classes = impact.affected_classes
        print(f"[E2E] Impacted classes downstream from UserRepository: {impacted_classes}")
        self.assertIn("UserService", impacted_classes)
        self.assertIn("UserController", impacted_classes)

        # ---------------------------------------------------------
        # 6. Diagnostics Checks
        # ---------------------------------------------------------
        print("[E2E] Validating Workspace Diagnostics...")
        diagnostics = DiagnosticsService()
        diag_report = diagnostics.run_diagnostics()
        print(f"[E2E] Diagnostics Status: {diag_report.overall_status}")
        print(f"[E2E] Diagnostics Warnings: {diag_report.warnings}")
        print(f"[E2E] Diagnostics Errors: {diag_report.errors}")
        self.assertEqual(diag_report.overall_status, "healthy")
        self.assertEqual(len(diag_report.errors), 0)

        # ---------------------------------------------------------
        # 7. Caching Behavior Verification
        # ---------------------------------------------------------
        print("[E2E] Checking Cache acceleration lookups...")
        from ecip_core.cache.manager import apply_cache_patches
        apply_cache_patches()
        cache_manager.clear()
        
        # 1st retrieval (Miss)
        t1_start = t1_end = t2_start = t2_end = 0
        retrieval.retrieve(query)
        stats1 = cache_manager.get_stats()
        self.assertGreaterEqual(stats1["misses"], 1)

        # 2nd retrieval (Hit)
        retrieval.retrieve(query)
        stats2 = cache_manager.get_stats()
        self.assertEqual(stats2["hits"], 1)
        print(f"[E2E] Cache Lookups Stats: {stats2}")


if __name__ == "__main__":
    unittest.main()
