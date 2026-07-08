# ECIP Lite — User Guide

**Version:** v1.0.0  
**Audience:** Developers using ECIP Lite to query their Java/Spring Boot codebase

---

## Table of Contents

1. [Installation](#installation)
2. [First-Time Setup](#first-time-setup)
3. [Indexing Your Project](#indexing-your-project)
4. [Querying the Codebase](#querying-the-codebase)
5. [Understanding Responses](#understanding-responses)
6. [Working with Multiple Projects](#working-with-multiple-projects)
7. [Using the REST API](#using-the-rest-api)
8. [Running Diagnostics](#running-diagnostics)
9. [Clearing the Index](#clearing-the-index)
10. [Tips & Best Practices](#tips--best-practices)

---

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) running locally

```bash
# Pull required models (one-time setup)
ollama pull nomic-embed-text   # for indexing
ollama pull qwen3.5:9b         # for answering questions
```

### Install ECIP Lite

```bash
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ecip-lite

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## First-Time Setup

Copy the example configuration and edit it:

```bash
cp .env.example .env
```

The key settings you must configure:

| Setting | Description | Default |
|---------|-------------|---------|
| `OLLAMA_BASE_URL` | URL of your running Ollama server | `http://localhost:11434` |
| `MODEL_NAME` | Chat LLM model for Q&A | `qwen3.5:9b` |
| `EMBEDDING_MODEL` | Embedding model for indexing | `nomic-embed-text` |
| `EMBEDDING_DIMENSION` | Vector dimensions (must match model) | `768` |

---

## Indexing Your Project

Place your Java project under the `projects/` directory:

```bash
cp -r /path/to/your/project projects/myproject
```

Then start ECIP Lite — it will index automatically on first run:

```bash
python -m ecip_core.main
```

You'll see real-time indexing progress:

```
[INFO] Index started
[INFO] Found 42 Java files
[INFO] File indexed: UserService.java
[INFO] File indexed: UserRepository.java
...
--- Indexing Summary Report ---
Files Indexed:   42
Files Skipped:   0
Chunks Embedded: 187 (in 24 batches)
Total Duration:  8.32s
```

### Incremental Indexing

After the first index, subsequent runs are fast — only changed files are re-indexed:

```
--- Indexing Summary Report ---
Files Indexed:   2       ← only the 2 you changed
Files Skipped:   40      ← unchanged files
Files Removed:   0
Total Duration:  0.83s
```

---

## Querying the Codebase

Type any natural language question:

```
Ask ECIP > What does UserService do?
Ask ECIP > Which classes depend on UserRepository?
Ask ECIP > What REST endpoints does UserController expose?
Ask ECIP > How does authentication work in this project?
Ask ECIP > What happens if I modify UserRepository?
Ask ECIP > Show me how findById is implemented
```

Type `exit` or `quit` to stop.

### Query Examples by Intent

| Intent | Example Query |
|--------|--------------|
| Explain a class | `What does OrderService do?` |
| Explain a method | `How does findByEmail work?` |
| Find REST endpoints | `What API endpoints does PaymentController have?` |
| Dependency lookup | `Which classes use UserRepository?` |
| Impact analysis | `What breaks if I change Product class?` |
| Navigation | `Where is the authentication logic?` |

---

## Understanding Responses

Each response includes:

```
═══════════════════════════════════════════════════════════════
 ECIP Response
═══════════════════════════════════════════════════════════════

UserService handles all user-related business logic including
creation, profile updates, and role assignment. It depends on
UserRepository for database operations and uses BCryptPasswordEncoder
for password hashing.

 Sources
───────────────────────────────────────────────────────────────
 [1] UserService.java:1-45          (class overview)
 [2] UserService.java:23-31         (createUser method)
 [3] UserRepository.java:1-20       (dependency)

 Completed in 1,243ms
═══════════════════════════════════════════════════════════════
```

- **Answer**: LLM-generated explanation grounded in your actual code
- **Sources**: Exact file and line references for every cited fact
- **Duration**: Total pipeline time

---

## Working with Multiple Projects

ECIP Lite supports indexing multiple independent projects simultaneously.

### Via REST API

```bash
# Register project A
curl -X POST http://localhost:8000/api/v1/workspaces \
  -H "Content-Type: application/json" \
  -d '{"project_id": "project_a", "alias": "Payment Service", "root_path": "projects/payment-service"}'

# Register project B
curl -X POST http://localhost:8000/api/v1/workspaces \
  -H "Content-Type: application/json" \
  -d '{"project_id": "project_b", "alias": "User Service", "root_path": "projects/user-service"}'

# Switch to project A
curl -X PUT http://localhost:8000/api/v1/workspaces/project_a/activate

# Now queries run against project A
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What does PaymentGateway do?"}'
```

Each project has its own isolated SQLite database and FAISS index — no cross-contamination.

---

## Using the REST API

Start the API server:

```bash
python run_api.py
```

API is at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Common API Calls

```bash
# Trigger indexing
curl -X POST http://localhost:8000/api/v1/index \
  -H "Content-Type: application/json" \
  -d '{"project_path": "projects/myproject"}'

# Query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What does UserService do?"}'

# List workspaces
curl http://localhost:8000/api/v1/workspaces

# Get active workspace stats
curl http://localhost:8000/api/v1/workspaces/active/stats
```

---

## Running Diagnostics

Check if your index is healthy:

```bash
curl http://localhost:8000/api/v1/diagnostics
```

Sample response:

```json
{
  "overall_status": "healthy",
  "checks": [
    {"name": "SQLite Integrity Check", "passed": true},
    {"name": "FAISS Index Availability", "passed": true},
    {"name": "Vector vs Chunk Count Check", "passed": true},
    {"name": "Source Files Existence Check", "passed": true},
    {"name": "Dependency Graph Consistency", "passed": true}
  ],
  "warnings": [],
  "errors": []
}
```

Status values:
- `healthy` — all checks passed
- `degraded` — warnings present but usable
- `unhealthy` — critical errors, re-index recommended

---

## Clearing the Index

To start fresh (e.g., after moving your project):

```bash
# Remove the FAISS index
rm -rf .ecip/

# Remove the SQLite database (replace with your project_id)
rm data/ecip_default.db

# Re-index
python -m ecip_core.main
```

---

## Tips & Best Practices

- **Index before querying** — ECIP needs to scan your project first. Always index before asking questions.
- **Specific questions work best** — "What does `UserService.createUser` do?" is better than "Explain the user stuff"
- **Use impact analysis for refactoring** — Before modifying a shared class, ask "What breaks if I change `X`?"
- **Use diagnostics if results seem wrong** — Run diagnostics to check if your index is stale or mismatched
- **Update the index after code changes** — Run the indexer again after making changes to keep answers accurate
- **Bigger embedding batch sizes** — If you have a fast machine, increase `EMBEDDING_BATCH_SIZE` in `.env` to speed up initial indexing
