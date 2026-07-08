# ECIP Lite 🚀

**ECIP Lite** (Enterprise Code Intelligence Platform — Lite) is an **offline, privacy-first AI code intelligence tool** built for developers who work with large Java/Spring Boot codebases.

It indexes your project locally, understands the structure of your code, and lets you ask natural language questions — without sending a single line of code to the cloud.

> 🔒 **100% local. No cloud. No API keys. No data leaves your machine.**

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/Zade-Samir/ECIP-lite/releases/tag/v1.0.0)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-255%20passing-brightgreen)](scripts/run_release_validation.py)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

---

## 🎯 What Problem Does It Solve?

When you join a new project or work on a large codebase, it's hard to:
- Understand what a service does without reading 1000 lines
- Find which classes depend on each other
- Know which method handles a specific API endpoint
- Trace what breaks if you change a shared class

ECIP Lite answers these questions using local AI — like having a senior developer who has read the entire codebase explain it to you.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **AST-Based Java Parser** | Understands classes, methods, annotations, generics, nested classes |
| 🧩 **Method-Level Chunking** | Indexes each method individually for precise search |
| 🗃️ **SQLite Metadata Store** | Stores rich structural metadata per file |
| 🔢 **Local Embeddings** | Uses `nomic-embed-text` via Ollama — no OpenAI needed |
| ⚡ **Incremental Indexing** | Only re-indexes files that actually changed |
| 💾 **Persistent FAISS Index** | Vector index survives restarts — no re-indexing needed |
| 🔄 **Batch Embedding** | Processes multiple chunks in one API call — faster indexing |
| 🔌 **Provider Abstraction** | Swap embedding/LLM backends without changing the pipeline |
| 🧠 **Hybrid Retrieval** | Exact metadata match + semantic vector search, merged and ranked |
| 🎯 **Intent Analyzer** | Understands what you're asking and routes retrieval intelligently |
| 🕸️ **Dependency Graph** | Tracks class-to-class dependencies and usage relationships |
| 💥 **Impact Analysis** | Shows which classes break if you change a given class |
| 📎 **Source Citations** | Every LLM answer is linked to exact `file:line` source references |
| 🔬 **Diagnostics** | 9-check system health validation — detects drift before it hurts |
| 🗂️ **Multi-Workspace** | Index and query multiple projects simultaneously, fully isolated |
| 🚀 **REST API** | FastAPI HTTP interface for all operations |
| 📊 **Performance Metrics** | Timing instrumentation across every pipeline stage |
| 🗄️ **Caching** | In-memory + disk cache with TTL and hit/miss stats |
| 📝 **Structured Logging** | Request-scoped correlation IDs, file rotation, JSON-compatible |

---

## 🏗️ Architecture

```
Java Project
      │
      ▼
Project Scanner          ← Finds all .java files (recursive)
      │
      ▼
AST Parser (javalang)    ← Classes, methods, annotations, constructors
      │
      ├──────────────────────────────────────────┐
      ▼                                          ▼
SQLite Metadata Store                    Dependency Graph
(classes, methods, edges)                (class relationships)
      │
      ▼
Smart Java Chunker        ← Method-level + class overview chunks
      │
      ▼
Embedding Service         ← nomic-embed-text via Ollama (batch)
      │
      ▼
FAISS Vector Store        ← Persistent local vector index
      │
      ▼
Hybrid Retrieval          ← Metadata match + semantic search, ranked
      │
      ├──────────────────┐
      ▼                  ▼
Context Builder     Intent Analyzer     ← Understand query intent
      │
      ▼
Prompt Builder           ← Structured prompt with code context
      │
      ▼
Inference Service         ← Ollama LLM (streaming/sync)
      │
      ▼
Citation Engine           ← Validates answer → file:line links
      │
      ▼
Response Formatter        ← CLI output or API JSON response
```

### 🔄 How it Works: Step-by-Step Data Flow

ECIP Lite operates via two primary runtime pipelines: **Indexing** and **Query Processing**.

#### 1. The Indexing Pipeline (Code Base to Local Database)
When you trigger a project index (via CLI or `POST /api/v1/index`):
1. **Scanning**: Recursively discovers all `.java` files in the project.
2. **Incremental Check**: Compares the SHA-256 hash of each file with the previously stored hash in SQLite. If unchanged, the file is skipped.
3. **AST Parsing**: Passes changed/new files through the Java AST parser (`javalang`) to extract classes, methods, parameters, annotations, and dependency imports.
4. **Dependency Mapping**: Populates a directed graph representing class dependency edges (`uses`, `depends_on`).
5. **Smart Chunking**: Splits files into method-level chunks (with signature contexts) plus a class-level overview chunk.
6. **Local Embedding**: Sends chunks in batches to Ollama's local `nomic-embed-text` endpoint to get 768-dimension vectors.
7. **Storage**: Persists structural metadata to SQLite and indexes vector representations to a disk-backed FAISS vector store.

#### 2. The Query Pipeline (Question to Cited Answer)
When you ask a question (like *"What does UserService do?"*):
1. **Entity Extraction**: Finds potential class names, method names, or endpoints in your query (e.g. `UserService`).
2. **Intent Analysis**: Determines if you are asking for code explanation, dependency traversal, endpoint lookup, or impact analysis.
3. **Hybrid Retrieval**:
   - Performs an exact metadata search in SQLite for parsed classes/methods matching the query.
   - Performs a semantic similarity search in the FAISS vector index using the query's embedding vector.
   - Merges and ranks the results, prioritizing exact metadata matches.
4. **Context Building**: Fetches the actual code snippets/chunks of the top-ranked files and organizes them.
5. **Prompt Assembly**: Injects the code context, rules, and question into a structured system prompt.
6. **Local LLM Inference**: Sends the prompt to Ollama's local LLM (`qwen3.5:9b`).
7. **Citation Verification**: Matches the LLM's response content against the injected file lines to generate verified `file:line` source tags.
8. **Formatting**: Renders a rich response showing the answer, source citations, execution metrics, and cache status.

---

## 🛠️ Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required |
| [Ollama](https://ollama.com/download) | Latest | For local LLM + embeddings |

### Pull required Ollama models

```bash
# Embedding model (required for indexing)
ollama pull nomic-embed-text

# LLM model (required for Q&A)
ollama pull qwen3.5:9b
```

> You can use any Ollama-compatible model. Update `MODEL_NAME` in `.env` accordingly.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ecip-lite
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your Ollama URL and model names. Key settings:

```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen3.5:9b
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
```

### 5. Add your Java project

Place your Java project under the `projects/` directory:

```bash
cp -r /path/to/your/spring-boot-project projects/myproject
```

### 6. Index your project (CLI)

```bash
# Register and index your project
python -m ecip_core.main
```

On first run, ECIP Lite will automatically scan and index the configured project.

### 7. Query your codebase

```bash
Ask ECIP > What does UserService do?
Ask ECIP > Which classes use UserRepository?
Ask ECIP > What happens if I change UserRepository?
Ask ECIP > Show me the REST endpoints in UserController
```

---

## 🌐 REST API

Start the API server:

```bash
python run_api.py
```

The API is now running at `http://localhost:8000`.

### Key Endpoints

```bash
# Index a project
POST /api/v1/index
{
  "project_path": "projects/myproject"
}

# Query the codebase
POST /api/v1/query
{
  "question": "What does UserService do?"
}

# List workspaces
GET /api/v1/workspaces

# Create a workspace
POST /api/v1/workspaces
{
  "project_id": "my_project",
  "alias": "My Spring Boot App",
  "root_path": "projects/myproject"
}

# Switch active workspace
PUT /api/v1/workspaces/{project_id}/activate

# Run diagnostics
GET /api/v1/diagnostics
```

> Interactive API docs are at `http://localhost:8000/docs` (Swagger UI).

---

## 📁 Project Structure

```
ecip-lite/
│
├── ecip_core/
│   ├── scanner/          ← Project file scanner
│   ├── parser/           ← AST-based Java parser
│   ├── chunking/         ← Method-level + class overview chunking
│   ├── embedding/        ← Embedding service + Ollama provider
│   ├── vectorstore/      ← Persistent FAISS index
│   ├── storage/sqlite/   ← SQLite repository + database setup
│   ├── indexing/         ← IndexBuilder (incremental pipeline)
│   ├── retrieval/        ← Hybrid retrieval, semantic search, context
│   ├── query/            ← Intent analyzer, entity extractor
│   ├── prompt/           ← Prompt builder
│   ├── inference/        ← LLM inference service + providers
│   ├── dependency/       ← Dependency graph + impact analysis
│   ├── citations/        ← Citation engine
│   ├── workspace/        ← Multi-project workspace manager
│   ├── diagnostics/      ← System health diagnostics
│   ├── cache/            ← Multi-level cache manager
│   ├── metrics/          ← Performance metrics collector
│   ├── logging/          ← Structured logging + correlation IDs
│   ├── api/              ← FastAPI REST API
│   ├── output/           ← Response formatter
│   ├── coordinator/      ← Query coordinator (pipeline orchestrator)
│   └── main.py           ← CLI entry point
│
├── tests/
│   ├── e2e/              ← End-to-end pipeline tests
│   ├── integration/      ← Integration tests
│   └── test_*.py         ← Unit tests per module
│
├── scripts/
│   └── run_release_validation.py  ← Pre-release gate (all 255 tests)
│
├── docs/
│   ├── RELEASE_CHECKLIST.md
│   ├── USER_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   └── ARCHITECTURE.md
│
├── projects/             ← Place your Java projects here
├── .env.example          ← Configuration template
├── requirements.txt      ← Python dependencies
├── run_api.py            ← API server entry point
├── CHANGELOG.md
├── RELEASE_NOTES.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## 🧪 Running Tests

```bash
# Run full release validation suite (recommended)
python scripts/run_release_validation.py

# Run all unit tests
python -m unittest discover tests/ -v

# Run specific test files
python -m unittest tests/test_parser.py -v
python -m unittest tests/test_faiss_store.py -v
python -m unittest tests/e2e/test_e2e_pipeline.py -v
```

---

## 📋 Roadmap

### v1.0.0 ✅ (Released)
- [x] AST-Based Java Parser
- [x] SQLite Metadata Store
- [x] Method-Level Chunking
- [x] Local Embedding Pipeline (Ollama)
- [x] Incremental Indexing
- [x] Persistent FAISS Index
- [x] Batch Embedding Processing
- [x] Semantic Search
- [x] Hybrid Retrieval (metadata + semantic)
- [x] Intent Analyzer
- [x] REST API (FastAPI)
- [x] Dependency Graph
- [x] Impact Analysis
- [x] Source Citations
- [x] Multi-Project Workspace Management
- [x] Diagnostics System
- [x] Performance Metrics
- [x] Multi-Level Caching
- [x] Structured Logging
- [x] End-to-End Test Suite (255 tests)

### v1.1 (Planned)
- [ ] Python language support
- [ ] Web UI (browser-based query interface)
- [ ] OpenAI / LM Studio embedding provider
- [ ] Dependency graph visualization

### v1.2 (Future)
- [ ] Multi-user support
- [ ] Docker deployment
- [ ] Go / JavaScript language support

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Branch naming conventions
- Commit message format
- Pull request process
- Testing requirements

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙋 Author

**Samir Zade**  
Building ECIP Lite as part of my #BuildInPublic journey.

Follow the progress on [LinkedIn](https://www.linkedin.com/in/samir-zade/)

---

> ⭐ If this project helps you, give it a star — it motivates continued development!
