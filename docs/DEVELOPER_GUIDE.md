# ECIP Lite — Developer Guide

**Version:** v1.0.0  
**Audience:** Developers contributing to or extending ECIP Lite

---

## Table of Contents

1. [Repository Layout](#repository-layout)
2. [Core Subsystems](#core-subsystems)
3. [Data Flow](#data-flow)
4. [Adding a New Language Parser](#adding-a-new-language-parser)
5. [Adding a New Embedding Provider](#adding-a-new-embedding-provider)
6. [Adding a New Diagnostic Check](#adding-a-new-diagnostic-check)
7. [API Development](#api-development)
8. [Testing Patterns](#testing-patterns)
9. [Configuration System](#configuration-system)
10. [Logging](#logging)
11. [Performance Metrics](#performance-metrics)
12. [Caching](#caching)

---

## Repository Layout

```
ecip-lite/
├── ecip_core/               ← All application code
│   ├── scanner/             ← File discovery
│   ├── parser/              ← Language parsers (Java)
│   ├── chunking/            ← Code chunking strategies
│   ├── embedding/           ← Embedding service + providers
│   ├── vectorstore/         ← FAISS vector index
│   ├── storage/sqlite/      ← SQLite database layer
│   ├── indexing/            ← Full indexing pipeline
│   ├── retrieval/           ← Hybrid search + context
│   ├── query/               ← Intent + entity extraction
│   ├── prompt/              ← Prompt construction
│   ├── inference/           ← LLM inference + providers
│   ├── dependency/          ← Dependency graph + impact
│   ├── citations/           ← Source citation engine
│   ├── workspace/           ← Multi-project workspace
│   ├── diagnostics/         ← System health checks
│   ├── cache/               ← Multi-level cache
│   ├── metrics/             ← Performance timers
│   ├── logging/             ← Structured logging
│   ├── api/                 ← FastAPI REST interface
│   ├── output/              ← Response formatting
│   ├── coordinator/         ← Query pipeline orchestrator
│   └── models/              ← Shared domain models
│
├── tests/                   ← All tests
│   ├── e2e/                 ← End-to-end tests
│   ├── integration/         ← Integration tests
│   └── test_*.py            ← Unit tests
│
├── scripts/                 ← Utility scripts
└── docs/                    ← Documentation
```

---

## Core Subsystems

### 1. Scanner (`ecip_core/scanner/`)
Recursively discovers `.java` files under a project root. Returns a list of absolute file paths.

### 2. Parser (`ecip_core/parser/`)
Receives a file path and produces a `ParsedJavaFile` containing:
- `class_name`, `package`, `annotations`, `imports`
- `List[MethodInfo]` — each with name, parameters, return type, start/end lines
- Dependency edges (which classes this file uses)

### 3. Chunker (`ecip_core/chunking/`)
Transforms a `ParsedJavaFile` into a list of `Chunk` objects — one per method plus a class overview chunk. Each chunk has `text`, `source_file`, `start_line`, `end_line`, `class_name`, `method_name`.

### 4. Embedding (`ecip_core/embedding/`)
- `EmbeddingService` wraps a `BaseEmbeddingProvider`
- `OllamaEmbeddingProvider` calls the Ollama embedding API
- Returns `numpy.ndarray` vectors; supports single and batch embedding

### 5. Vector Store (`ecip_core/vectorstore/`)
- `FAISSStore` wraps `faiss.IndexFlatIP` with cosine similarity
- Persistent: saves to disk after every write; loads on startup
- Supports add, search (top-K with scores), delete by ID, rebuild

### 6. Storage (`ecip_core/storage/sqlite/`)
- `Database` manages SQLite connections (per-workspace)
- `JavaRepository` provides CRUD operations for `java_files` and `java_methods` tables

### 7. Index Builder (`ecip_core/indexing/`)
Orchestrates the full indexing pipeline:
1. Scan project files
2. For each file: hash → compare → skip/parse/remove
3. Chunk → embed (batch) → store in FAISS + SQLite
4. Build dependency edges

### 8. Retrieval (`ecip_core/retrieval/`)
- `SemanticSearch` — FAISS top-K with confidence filtering
- `MetadataService` — Exact class/method lookup in SQLite
- `HybridRetrieval` — Merges both, deduplicates, sorts by rank
- `ContextBuilder` — Fetches chunk texts for LLM context

### 9. Query Intelligence (`ecip_core/query/`)
- `IntentAnalyzer` — Rule-based intent classification into 7 categories
- `EntityExtractor` — Extracts class names, method names, endpoint paths from raw query text

### 10. Inference (`ecip_core/inference/`)
- `InferenceService` — Dispatches to configured provider
- `OllamaProvider` — Sends prompt to Ollama chat API
- Supports sync and streaming modes

### 11. Dependency Graph (`ecip_core/dependency/`)
- `DependencyService` — Stores and queries class relationship edges
- `ImpactAnalysisEngine` — BFS/DFS traversal to compute blast radius of a change

### 12. Workspace (`ecip_core/workspace/`)
- `WorkspaceManager` — Registry of all projects; tracks active workspace
- Each workspace gets its own `data/ecip_{project_id}.db` and `.ecip/faiss_{project_id}.index`
- `Database` class dynamically switches connections on workspace change

### 13. Cache (`ecip_core/cache/`)
- `CacheManager` — Wraps `MemoryCache` + `DiskCache`
- `cached()` decorator for transparent function result caching
- `apply_cache_patches()` — Monkey-patches service methods at startup

### 14. Coordinator (`ecip_core/coordinator/`)
- `QueryCoordinator` — Orchestrates: entity extract → retrieve → context build → prompt build → infer → cite → format

---

## Data Flow

```
User Query
    │
    ▼
EntityExtractor         → extract class/method names
    │
    ▼
IntentAnalyzer          → classify query type
    │
    ▼
HybridRetrieval         → metadata match + semantic search
    │
    ▼
ContextBuilder          → fetch chunk texts
    │
    ▼
PromptBuilder           → build structured prompt
    │
    ▼
InferenceService        → LLM response
    │
    ▼
CitationEngine          → map answer → file:line refs
    │
    ▼
ResponseFormatter       → render CLI / JSON output
```

---

## Adding a New Language Parser

1. Create `ecip_core/parser/<language>/` package
2. Implement `BaseParser` interface:

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> ParsedFile:
        ...
```

3. Return the same `ParsedFile` / `ParsedJavaFile`-equivalent domain model
4. Register the parser in `IndexBuilder.get_parser(file_path)` by extension
5. Add integration tests in `tests/test_<language>_parser.py`

---

## Adding a New Embedding Provider

1. Create `ecip_core/embedding/providers/<name>_provider.py`
2. Extend `BaseEmbeddingProvider`:

```python
class MyProvider(BaseEmbeddingProvider):
    def embed(self, text: str) -> np.ndarray: ...
    def embed_batch(self, texts: list[str]) -> list[np.ndarray]: ...
```

3. Register in `EmbeddingService.__init__` based on `settings.EMBEDDING_PROVIDER`
4. Add unit tests in `tests/test_embedding.py`

---

## Adding a New Diagnostic Check

1. Open `ecip_core/diagnostics/service.py`
2. Add a method `def check_<name>(self) -> Tuple[bool, Optional[str]]:`
3. Register it in `DiagnosticsService.run_diagnostics()`:

```python
checks = [
    ("My New Check", self.check_my_new_check),
    ...
]
```

4. Add a test case in `tests/test_diagnostics.py`

---

## API Development

The REST API lives in `ecip_core/api/`:
- `main.py` — FastAPI app factory
- `routes/` — Endpoint routers per feature area

### Adding a New Endpoint

```python
# ecip_core/api/routes/myfeature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/myfeature")
def my_endpoint():
    return {"status": "ok"}

# Register in ecip_core/api/main.py
app.include_router(router, prefix="/api/v1")
```

---

## Testing Patterns

### Unit Test

```python
class TestMyService(unittest.TestCase):
    def setUp(self):
        self.service = MyService()

    def test_happy_path(self):
        result = self.service.do_something("input")
        self.assertEqual(result, expected)
```

### Test with SQLite

Use the `testing` profile — it uses an in-memory DB:

```python
os.environ["ECIP_PROFILE"] = "testing"
```

### Test with Mocked Ollama

```python
@patch("ecip_core.inference.providers.ollama_provider.OllamaProvider.generate")
def test_inference(self, mock_generate):
    mock_generate.return_value = "mocked response"
    ...
```

### E2E Test Pattern

See `tests/e2e/test_e2e_pipeline.py` for the full pattern — workspace setup, indexing, querying, teardown.

---

## Configuration System

All settings are in `ecip_core/config/settings.py` using `pydantic-settings`.

```python
from ecip_core.config.settings import settings

# Access any setting
settings.OLLAMA_BASE_URL
settings.EMBEDDING_DIMENSION
settings.CACHE_ENABLED
```

Settings are loaded from `.env` with profile-based defaults. Do not hardcode values — always use `settings.*`.

---

## Logging

```python
from ecip_core.logging import get_logger

logger = get_logger(__name__)

logger.info("Operation started")
logger.warning("Low confidence score")
logger.error("Connection failed")
```

All log calls automatically inject the active `correlation_id` from context.

---

## Performance Metrics

```python
from ecip_core.metrics.collector import MetricsCollector

collector = MetricsCollector()

with collector.timer("my_operation"):
    # ... your code ...
    pass

report = collector.get_report()
print(report.summary())
```

---

## Caching

To cache a function's return value:

```python
from ecip_core.cache.manager import cache_manager

@cache_manager.cached(ttl=3600)
def expensive_function(query: str):
    ...
```

Or apply at runtime via `apply_cache_patches()` for monkey-patching service methods without modifying them.
