# ECIP Lite v1.0.0 — Release Notes

**Release Date:** July 9, 2026  
**Version:** `v1.0.0`  
**Codename:** _First Light_

---

## 🎉 Overview

ECIP Lite v1.0.0 is the **first stable, production-quality release** of the Enterprise Code Intelligence Platform — Lite.

This release marks the culmination of 13 development sprints, delivering a fully offline, privacy-first AI code intelligence tool designed for Java/Spring Boot developers. Every core subsystem — parsing, indexing, retrieval, inference, diagnostics, and workspace management — has been built, tested, and validated.

---

## ✨ What's New in v1.0.0

### 🔍 Core Intelligence
- **AST-Based Java Parser** — Full class, method, annotation, and constructor extraction using `javalang`
- **Method-Level Smart Chunker** — Each method is indexed as an independent searchable unit
- **Semantic Search** — FAISS-backed vector similarity search using local Ollama embeddings
- **Hybrid Retrieval** — Combines exact metadata lookup with semantic search, ranked by confidence
- **Intent Analyzer** — Classifies query types (`explain_code`, `dependency_analysis`, `endpoint_lookup`, etc.) to route retrieval intelligently

### 🗄️ Storage & Indexing
- **SQLite Metadata Store** — Stores class hierarchy, method signatures, annotations, and dependency edges
- **FAISS Vector Store** — Persistent, disk-backed local vector index; survives restarts with no re-indexing
- **Incremental Indexing** — Hash-based file diffing; only changed files are re-indexed
- **Batch Embedding** — Processes multiple chunks per Ollama API call for faster indexing

### 🤖 Inference
- **Multi-Provider LLM Support** — Ollama (primary), with provider abstraction for future backends
- **Prompt Builder** — Intent-aware structured prompts with injected code context
- **Context Builder** — Fetches and ranks relevant code snippets for LLM prompt construction
- **Source Citations** — Validates and links every LLM answer to exact file:line ranges

### 📡 API
- **FastAPI REST API** — Full HTTP interface for indexing, querying, workspace, and diagnostics
- **Multi-Project Workspace Management** — Register, switch, and isolate multiple independent project indexes
- **Streaming Support** — Token-level streaming inference via Server-Sent Events

### 🔧 Operations
- **Diagnostics Service** — 9-check health validation: SQLite, FAISS, vector counts, source files, orphaned metadata, dependency graph, cache, config, workspace validity
- **Performance Metrics** — Pipeline-wide timing instrumentation across all subsystems
- **Multi-Level Caching** — In-memory + disk cache with TTL, invalidation, and hit/miss statistics
- **Structured Logging** — Request-scoped correlation IDs, JSON-compatible log output, file rotation

### ✅ Testing
- **255 Automated Tests** — Unit, integration, E2E, and release gating tests
- **End-to-End Pipeline Test** — Full pipeline validation from cold-index to LLM response
- **Release Validation Suite** — `python scripts/run_release_validation.py` — single-command pre-release gate

---

## 🏗️ Architecture at v1.0.0

```
Java Project
      │
      ▼
Project Scanner          ← Finds all .java files (recursive)
      │
      ▼
AST Parser (javalang)    ← Classes, methods, annotations, generics
      │
      ├──────────────────────────────────────────┐
      ▼                                          ▼
SQLite Metadata Store                    Dependency Graph
(classes, methods, files)                (edges: uses/imports)
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
Context Builder     Intent Analyzer    ← Understand query intent
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

---

## 🐛 Known Limitations

- **Java only** — Python, JavaScript, Go support planned for v1.1
- **Ollama required** — No native OpenAI or cloud LLM support in this release
- **Single-machine** — No distributed or multi-user deployment in v1.0
- **No Web UI** — API + CLI only; browser UI planned for v1.2

---

## 🔄 Upgrade Guide

This is the first public release — no migration is required.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `faiss-cpu` | 1.14.3 | Vector similarity search |
| `ollama` | 0.6.2 | Local LLM + embedding API |
| `fastapi` | 0.139.0 | REST API framework |
| `uvicorn` | 0.51.0 | ASGI server |
| `javalang` | 0.13.0 | Java AST parser |
| `pydantic` | 2.13.4 | Data validation |
| `pydantic-settings` | 2.14.2 | Config management |
| `python-dotenv` | 1.2.2 | `.env` loading |
| `numpy` | 2.5.0 | Vector math |
| `httpx` | 0.28.1 | HTTP client |
| `click` | 8.4.2 | CLI framework |

---

## 🙏 Acknowledgements

Built with ❤️ as part of the #BuildInPublic journey by **Samir Zade**.

---

_ECIP Lite v1.0.0 — First Light_
