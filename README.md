# ECIP Lite 🚀

**ECIP Lite** (Enterprise Code Intelligence Platform — Lite) is an **offline, privacy-first AI code intelligence tool** built for developers who work with large Java/Spring Boot codebases.

It indexes your project locally, understands the structure of your code, and lets you ask natural language questions — without sending a single line of code to the cloud.

> 🔒 **100% local. No cloud. No API keys. No data leaves your machine.**

---

## 🎯 What Problem Does It Solve?

When you join a new project or work on a large codebase, it's hard to:
- Understand what a service does without reading 1000 lines
- Find which classes depend on each other
- Know which method handles a specific feature

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
| 🔌 **Provider Abstraction** | Swap embedding backends without changing the pipeline |
| 🧠 **Semantic Search** | Find the right method/class using natural language |
| 🔑 **Spring Boot Support** | Understands `@RestController`, `@Service`, `@Repository`, constructor injection |

---

## 🏗️ Architecture

```
Java Project
      │
      ▼
Project Scanner          ← Finds all .java files
      │
      ▼
AST Parser (javalang)    ← Parses classes, methods, annotations
      │
      ▼
SQLite Metadata Store    ← Persists structural metadata
      │
      ▼
Java Chunker             ← Method-level + class overview chunks
      │
      ▼
Embedding Service        ← nomic-embed-text via Ollama (batch)
      │
      ▼
FAISS Vector Store       ← Persistent local vector index
      │
      ▼
Semantic Retrieval       ← Top-K similarity search
      │
      ▼
LLM (Ollama)             ← Answers your question with context
```

---

## 🛠️ Prerequisites

Before you start, install these:

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

Copy the example config and edit it:

```bash
cp .env.example .env
```

Or create `.env` manually:

```env
# Ollama server URL
OLLAMA_BASE_URL=http://localhost:11434

# LLM model for Q&A
MODEL_NAME=qwen3.5:9b

# Embedding model
EMBEDDING_MODEL=nomic-embed-text

# Embedding vector dimensions (must match the model)
EMBEDDING_DIMENSION=768

# Batch size for embedding generation
EMBEDDING_BATCH_SIZE=8

# Generation settings
TEMPERATURE=0.2
TOP_P=0.9
MAX_TOKENS=4096
STREAM=false

# System prompt
SYSTEM_PROMPT="You are ECIP, an expert Java and Spring Boot Architect."
```

### 5. Run the assistant

```bash
python -m ecip_core.main
```

Type your question and press Enter. Type `exit` or `quit` to stop.

---

## 📁 Project Structure

```
ecip-lite/
│
├── ecip_core/
│   ├── scanner/          ← Project file scanner
│   ├── parser/
│   │   ├── java/         ← AST-based Java parser
│   │   └── models/       ← ParsedJavaFile, MethodInfo domain models
│   ├── chunking/         ← Method-level + class overview chunking
│   ├── embedding/
│   │   ├── providers/    ← OllamaEmbeddingProvider (swappable)
│   │   └── models/       ← Embedding model
│   ├── vectorstore/      ← Persistent FAISS index
│   ├── storage/
│   │   └── sqlite/       ← SQLite repository + database setup
│   ├── indexing/         ← IndexBuilder (incremental pipeline)
│   ├── retrieval/        ← Semantic search service
│   ├── inference/        ← LLM inference + settings
│   └── common/           ← Shared logger, utilities
│
├── tests/                ← Unit + integration tests
├── prompts/              ← Implementation playbook
├── requirements.txt
└── .env
```

---

## 🧪 Running Tests

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests
python -m unittest discover tests/

# Run a specific test file
python -m unittest tests/test_parser.py -v
python -m unittest tests/test_faiss_store.py -v
python -m unittest tests/test_embedding.py -v
python -m unittest tests/test_index_builder.py -v
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/ECIP-lite.git
cd ecip-lite
```

### 2. Create a feature branch

```bash
git checkout -b feat/your-feature-name
```

### 3. Make changes and run tests

```bash
python -m unittest discover tests/
```

All tests must pass before submitting a PR.

### 4. Open a Pull Request

- Describe what you changed and why
- Link any related issues
- Keep PRs focused — one feature or fix per PR

### Areas open for contribution

- 🌐 Support for other languages (Python, JavaScript, Go)
- 🔌 New embedding providers (OpenAI, llama.cpp, LM Studio)
- 🖥️ REST API / Web UI
- 📊 Dependency graph visualization
- 📝 Better prompt engineering
- 🔒 Security & access control features

---

## 📋 Roadmap

- [x] Project Scanner
- [x] AST-Based Java Parser
- [x] Spring Boot Annotation Extraction
- [x] SQLite Metadata Store
- [x] Method-Level Chunking
- [x] Local Embedding Pipeline (Ollama)
- [x] Incremental Indexing
- [x] Persistent FAISS Index
- [x] Batch Embedding Processing
- [x] Embedding Provider Abstraction
- [ ] Semantic Search Service
- [ ] REST API (FastAPI)
- [ ] Web UI
- [ ] Dependency Graph
- [ ] Multi-language Support

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙋 Author

**Samir Zade**
Building ECIP Lite as part of my #BuildInPublic journey.

Follow the progress on [LinkedIn](https://www.linkedin.com/in/samirzade)

---

> ⭐ If this project helps you, give it a star — it motivates continued development!
