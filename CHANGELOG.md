# Changelog

All notable changes to ECIP Lite are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-07-09

### 🎉 First Stable Release — _First Light_

---

### Added

#### Sprint 1 — Core Foundation
- Project scanner: recursive `.java` file discovery with path normalization
- AST-based Java parser using `javalang`: class, method, annotation, constructor extraction
- `ParsedJavaFile` and `MethodInfo` domain models

#### Sprint 2 — Persistence & Storage
- SQLite metadata store: `java_files` and `java_methods` schema
- `JavaRepository` with full CRUD: insert, upsert, delete, search by class/method
- Database connection pooling and auto-initialization

#### Sprint 3 — Embeddings & Vectors
- `OllamaEmbeddingProvider` with `nomic-embed-text` support
- Provider abstraction layer (`BaseEmbeddingProvider`) for future swap
- Persistent FAISS index with save/load across restarts
- Batch embedding: multiple chunks per Ollama API call

#### Sprint 4 — Indexing Pipeline
- `IndexBuilder` incremental indexing with SHA-256 file hash comparison
- Skip unchanged files; remove stale vectors and metadata on deletion
- Indexed summary report: files indexed/skipped/removed, duration, batch count

#### Sprint 5 — Retrieval & Search
- Semantic search service with configurable top-K FAISS results
- Confidence score filtering with low-confidence warnings
- Exact metadata lookup: search by class name, method name
- `HybridRetrieval`: deterministic metadata match + semantic merge, deduplication

#### Sprint 6 — Inference & Output
- `InferenceService` with Ollama LLM integration
- Multi-provider abstraction (`BaseProvider`) — Ollama primary
- Streaming inference via Server-Sent Events
- `PromptBuilder` with intent-aware structured prompts
- `ResponseFormatter`: rich CLI output with sections and citations
- `ContextBuilder`: retrieves and ranks top-K chunks for prompt injection

#### Sprint 7 — API Layer
- FastAPI REST API with full project endpoints
- `/api/v1/index` — trigger indexing
- `/api/v1/query` — submit natural language queries
- `/api/v1/workspaces` — multi-project workspace CRUD
- `/api/v1/diagnostics` — health check endpoint
- Request/response Pydantic models with validation
- CORS support for local development

#### Sprint 8 — Dependency Graph
- Dependency graph builder: extracts class-to-class `uses`/`imports` edges
- `DependencyService` with graph traversal queries
- `ImpactAnalysisEngine`: computes blast radius for a changed class
- `ImpactReport` with affected classes list

#### Sprint 9 — Citations & Query Intelligence
- `CitationEngine`: validates and maps LLM answer spans to `file:line` ranges
- `EntityExtractor`: extracts class names, method names, endpoints from raw query text
- `IntentAnalyzer`: classifies query intent (`explain_code`, `dependency_analysis`, `endpoint_lookup`, `impact_analysis`, `navigation`, `semantic_question`)
- `QueryCoordinator`: orchestrates full pipeline from query → response

#### Sprint 10 — Logging & Observability
- Structured logging with `correlation_id` injection per request
- Rotating file handler with configurable max size and backup count
- `safe_log` decorator: logs exceptions without crashing the application
- JSON-compatible log formatter for log shipping

#### Sprint 11 — Performance Metrics
- `MetricsCollector`: named timers, nested spans, total duration tracking
- Per-stage metrics: scanning, parsing, chunking, embedding, indexing, retrieval, inference, E2E
- `MetricsReport` with tabular summary export
- Metrics instrumented across `IndexBuilder`, `HybridRetrieval`, `InferenceService`

#### Sprint 12 — Workspace & Diagnostics
- `WorkspaceManager`: register, list, switch, delete isolated project workspaces
- Per-project SQLite databases and FAISS indexes (fully isolated)
- Project aliases, active workspace selection, workspace statistics
- `DiagnosticsService` with 9 health checks:
  - SQLite integrity (PRAGMA)
  - Workspace directory validity
  - FAISS index availability and readability
  - Vector count vs chunk count sync
  - Source file existence on disk
  - Orphaned metadata detection
  - Dependency graph consistency
  - Cache consistency
  - Configuration validation
- `DiagnosticsReport`: `healthy`, `degraded`, or `unhealthy` overall status with per-check results

#### Sprint 13 — Release & Validation
- Multi-level cache (`CacheManager`): in-memory + disk with TTL, invalidation, hit/miss tracking
- Cache monkey-patching: wraps `EmbeddingService`, `InferenceService`, `HybridRetrieval`, `ContextBuilder`, `PromptBuilder`, `SemanticSearch`
- End-to-end pipeline test (`tests/e2e/test_e2e_pipeline.py`): full pipeline from cold index to LLM response in a single isolated test
- Release validation script (`scripts/run_release_validation.py`): auto-discovers all 255 tests, produces tabular summary, outputs `release_validation_report.json`, exits with gate status
- `docs/RELEASE_CHECKLIST.md` pre-release verification checklist
- `CHANGELOG.md`, `RELEASE_NOTES.md`, `CONTRIBUTING.md` documentation

---

### Changed

- Settings system unified under `pydantic-settings` with profile support (`development`, `testing`, `production`)
- `Database` class refactored to support per-workspace connection switching
- `IndexBuilder` updated to propagate dependency edges during indexing
- `HybridRetrieval` updated to accept entity hints from `EntityExtractor`

---

### Fixed

- FAISS persistence: index not saved after batch embedding — fixed via explicit `save()` call
- SQLite connection leak when workspace was switched mid-request — fixed with `close()` on path change
- Chunk count mismatch in diagnostics: now counts `java_methods + java_files` for accurate comparison
- E2E test isolation: cache patches now restored after each test via `setUp`/`tearDown` backup

---

## [Unreleased]

### Planned for v1.1
- Python language support
- Web UI (browser-based query interface)
- OpenAI / LM Studio embedding provider
- Dependency graph visualization

---

[1.0.0]: https://github.com/Zade-Samir/ECIP-lite/releases/tag/v1.0.0
