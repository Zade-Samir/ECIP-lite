# ECIP Lite — Architecture Overview

**Version:** v1.0.0

---

## System Overview

ECIP Lite is a fully local, privacy-first code intelligence platform. It indexes Java/Spring Boot projects into a hybrid search system combining SQLite metadata storage and FAISS vector embeddings. Natural language queries are answered by a local LLM with retrieved code context and validated source citations.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                                                                 │
│         CLI (python -m ecip_core.main)                         │
│         REST API (FastAPI — run_api.py)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Query Coordinator                           │
│                 (ecip_core/coordinator/)                        │
│                                                                 │
│  EntityExtractor → IntentAnalyzer → HybridRetrieval            │
│  ContextBuilder → PromptBuilder → InferenceService             │
│  CitationEngine → ResponseFormatter                            │
└──────────┬───────────────────────────────┬──────────────────────┘
           │                               │
           ▼                               ▼
┌────────────────────┐       ┌────────────────────────────────────┐
│   Indexing Layer   │       │         Storage Layer              │
│                    │       │                                    │
│  Scanner           │       │  SQLite (java_files,              │
│  Parser (AST)      │       │          java_methods,            │
│  Chunker           │◄─────►│          dependencies,            │
│  Embedding Service │       │          workspaces)              │
│  IndexBuilder      │       │                                    │
│                    │       │  FAISS (vector index,             │
└────────────────────┘       │          metadata.pkl)            │
                             └────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Intelligence Layer                           │
│                                                                 │
│  Dependency Graph    Diagnostics Service    Cache Manager      │
│  Impact Analysis     Workspace Manager      Metrics Collector  │
│  Performance Metrics Structured Logging                        │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Ollama (Local)                           │
│                                                                 │
│  nomic-embed-text (embeddings)   qwen2.5-coder:3b (LLM inference)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Module | Responsibility |
|-----------|--------|---------------|
| **Scanner** | `scanner/` | Discover all `.java` files in project tree |
| **Parser** | `parser/java/` | AST extraction: classes, methods, annotations |
| **Chunker** | `chunking/` | Split parsed files into searchable chunks |
| **Embedding Service** | `embedding/` | Generate float vectors from text chunks |
| **FAISS Store** | `vectorstore/` | Persistent local vector similarity index |
| **SQLite Repository** | `storage/sqlite/` | Structured metadata storage and queries |
| **Index Builder** | `indexing/` | Orchestrate full incremental indexing pipeline |
| **Semantic Search** | `retrieval/` | Top-K FAISS vector similarity search |
| **Metadata Service** | `retrieval/metadata/` | Exact class/method name lookup in SQLite |
| **Hybrid Retrieval** | `retrieval/` | Merge + rank metadata and semantic results |
| **Context Builder** | `retrieval/context/` | Fetch and format chunk text for LLM prompt |
| **Intent Analyzer** | `query/` | Classify query into 7 intent categories |
| **Entity Extractor** | `query/` | Extract class/method/endpoint names from query |
| **Prompt Builder** | `prompt/` | Build structured prompt with code context |
| **Inference Service** | `inference/` | Dispatch query to LLM provider |
| **Citation Engine** | `citations/` | Map LLM answer spans to file:line references |
| **Response Formatter** | `output/` | Render structured CLI / JSON output |
| **Dependency Graph** | `dependency/` | Track class-to-class relationship edges |
| **Impact Analysis** | `dependency/` | Compute blast radius of a class change |
| **Workspace Manager** | `workspace/` | Isolate multiple project indexes |
| **Diagnostics** | `diagnostics/` | 9-check system health validation |
| **Cache Manager** | `cache/` | In-memory + disk cache with TTL |
| **Metrics Collector** | `metrics/` | Per-stage timing instrumentation |
| **Structured Logger** | `logging/` | Request-scoped correlation ID logging |
| **Query Coordinator** | `coordinator/` | Orchestrate full query pipeline |
| **REST API** | `api/` | FastAPI HTTP interface for all operations |

---

## Data Models

### Indexing Models

```
ParsedJavaFile
├── file_path: str
├── class_name: str
├── package: str
├── annotations: List[str]
├── imports: List[str]
├── methods: List[MethodInfo]
└── dependencies: List[str]       ← classes this file uses

MethodInfo
├── name: str
├── parameters: List[str]
├── return_type: str
├── annotations: List[str]
├── start_line: int
└── end_line: int

Chunk
├── text: str
├── source_file: str
├── class_name: str
├── method_name: Optional[str]
├── start_line: int
└── end_line: int
```

### Retrieval Models

```
HybridResult
├── text: str
├── source_file: str
├── class_name: str
├── method_name: Optional[str]
├── start_line: int
├── end_line: int
├── score: float
└── source: str         ← "metadata" | "semantic"
```

### Response Models

```
ECIPResponse
├── answer: str
├── citations: List[Citation]
├── intent: str
├── duration_ms: float
└── metadata: dict

Citation
├── file_path: str
├── start_line: int
├── end_line: int
└── snippet: str
```

---

## Key Design Decisions

### 1. Hybrid Retrieval
Pure semantic search misses exact matches (e.g., "show me UserRepository"). Pure metadata lookup misses semantic queries ("find the payment processing code"). Hybrid merges both with metadata results ranked first.

### 2. Incremental Indexing
SHA-256 file hashes detect changes. Only modified files are re-parsed and re-embedded. This keeps re-indexing fast (< 1s for unchanged projects).

### 3. Per-Workspace Isolation
Each project gets its own SQLite database and FAISS index file. The `WorkspaceManager` switches the active database connection dynamically. No cross-project contamination is possible.

### 4. Cache as Monkey-Patch
The cache layer wraps service methods at runtime via `apply_cache_patches()` without modifying business logic files. This keeps core subsystems clean and independently testable.

### 5. Provider Abstraction
Both embeddings and LLM inference use a `BaseProvider` pattern. Swapping from Ollama to a different backend requires only implementing the provider interface — the rest of the pipeline is unchanged.

---

## File Storage Layout

```
ecip-lite/
├── data/
│   ├── ecip.db                     ← Master workspace registry
│   ├── ecip_default.db             ← Default project database
│   └── ecip_{project_id}.db        ← Per-project databases
│
├── .ecip/
│   ├── faiss.index                 ← Default project vector index
│   ├── faiss_meta.pkl              ← Default project metadata
│   ├── faiss_{project_id}.index    ← Per-project indexes
│   └── faiss_{project_id}_meta.pkl
│
└── logs/
    └── ecip.log                    ← Application log file
```

---

## Security Model

- **No network egress**: all LLM and embedding calls go to local Ollama
- **No authentication in v1.0**: REST API is intended for local/LAN use only
- **No code transmission**: source files are read locally; only embeddings (float arrays) are stored
- **SQLite**: plain file, no encryption; secure your filesystem

---

## Performance Characteristics

| Operation | Typical Time |
|-----------|-------------|
| Initial index (50 files) | 5–15 seconds |
| Incremental re-index (2 files) | < 1 second |
| Query (cold cache) | 1–3 seconds |
| Query (warm cache) | < 100ms |
| Diagnostics check | < 50ms |
| Impact analysis | < 10ms |
