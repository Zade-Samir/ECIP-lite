# ECIP Enterprise 🚀

**ECIP (Enterprise Code Intelligence Platform)** is an **offline, privacy-first AI Code Intelligence & Autonomous Software Engineering Platform** built for high-security enterprise teams working with complex Java/Spring Boot codebases, microservices, and distributed architectures.

It indexes your projects locally, constructs a multi-hop Knowledge Graph, understands cross-repository dependencies, and deploys autonomous AI agents to pair-program, debug, review code, generate tests, manage architecture, and validate release readiness — **without a single line of code ever leaving your machine**.

> 🔒 **100% Offline. 0% Cloud. Zero API Key Leaks. Complete Privacy Guarantee.**

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/Zade-Samir/ECIP-lite/releases/tag/v1.0.0)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-532%20passing-brightgreen)](scripts/release/build_release.py)
[![Prompts Completed](https://img.shields.io/badge/playbook-100%2F100%20Prompts-success)](#-100-prompt-enterprise-milestone)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

---

## 🎯 What Problem Does ECIP Solve?

Enterprise software development faces three critical challenges:
1. 🔒 **Data Privacy Constraints**: Financial institutions, healthcare, and defense organizations cannot upload proprietary code to cloud AI providers (ChatGPT, GitHub Copilot).
2. 👁️ **Context Tunnel Vision**: Standard LLM tools lack deep understanding of multi-service dependencies, SQL schemas, configuration profiles, and layer architecture ($A \to B \to C$).
3. ⏳ **Developer Time Drain**: Engineers spend 60%+ of their time tracing class relationships, manually testing, debugging stack traces, refactoring legacy code, and writing documentation.

**ECIP Enterprise** solves all three by providing a local, RAG + Knowledge Graph-powered autonomous engineering engine embedded directly in your workflow.

---

## ✨ Enterprise Feature Highlights

### 🤖 Autonomous AI Copilots & Assistants (Prompts 091–100)
- 👥 **AI Pair Programmer**: Workspace-aware chat assistant with verified `file:line` source citations.
- 🐞 **AI Debugging Assistant**: Correlates stack traces and log lines to pinpoint root causes and recommend fixes.
- 🔍 **AI Code Review Assistant**: Automated PR reviewer with inline comments for quality, security, and performance.
- 🧪 **AI Test Generation Assistant**: Automatically builds JUnit/Pytest test suites, mocks, and fixtures with coverage impact estimation.
- 📄 **AI Documentation Assistant**: Generates and updates Markdown/HTML API references, architecture guides, and stale doc checks.
- 🏗️ **AI Architecture Copilot**: Recommends design patterns, evaluates trade-offs, and drafts Architectural Decision Records (ADRs).
- 🚀 **AI DevOps Copilot**: Analyzes Dockerfiles, Kubernetes manifests, and Helm charts for resource limits and security misconfigurations.
- 🎛️ **AI Platform Operations Center**: Central console for monitoring service topology, incidents, and 30-day storage/capacity forecasting.
- 🤖 **Autonomous Engineering Platform**: Multi-agent orchestrator executing end-to-end goals (Planner $\to$ Executor $\to$ Verifier $\to$ Self-Healing).

### 🔍 Intelligence, Security & Quality (Prompts 076–090)
- 🛡️ **Security Intelligence & Secret Scanner**: AST-based detector for hardcoded tokens, RSA keys, SQL injections, and weak crypto.
- 🚦 **Release Readiness Intelligence**: Evaluates blocking/advisory gates to calculate 0–100 release scores and GO / NO-GO decisions.
- 📈 **Continuous Code Quality Intelligence**: Tracks maintainability index, cyclomatic complexity, duplication, and technical debt trends.
- 🔄 **Refactoring Automation Engine**: Reversible AST transformations (package rename, API migration) with dry-run unified diffs and rollback.
- 🛠️ **Code Modernization Assistant**: Upgrade planner for Java version transitions and Spring Boot 2.x $\to$ 3.x migrations.
- ⚡ **CI/CD Intelligence**: Adapters for GitHub Actions, GitLab CI, and Jenkins with automated PR build annotations.

### 🧠 Core Retrieval & Graph Engines (Prompts 001–075)
- 🕸️ **Knowledge Graph Engine**: Multi-hop graph traversal (SQLite / Neo4j) mapping `CALLS`, `DEPENDS_ON`, `IMPLEMENTS`, and `EXTENDS`.
- 🔎 **Hybrid Search (BM25 + FAISS Vector)**: Lexical keyword search combined with dense vector semantic search.
- 🎯 **Cross-Encoder Re-ranking**: Second-stage scoring for maximum precision on complex queries.
- 🌐 **Interactive Knowledge Dashboard**: Visual web console served live at `http://localhost:8000/dashboard/ui`.

---

## 🏗️ Architecture

```text
                               ┌───────────────────────────────────────────────┐
                               │             Enterprise Clients                │
                               │   (VS Code, IntelliJ, CLI, REST API)          │
                               └──────────────────────┬────────────────────────┘
                                                      │
                                                      ▼
                               ┌───────────────────────────────────────────────┐
                               │              Enterprise API Gateway           │
                               │    (RBAC, Multi-Tenancy, Audit Logging)       │
                               └──────────────────────┬────────────────────────┘
                                                      │
              ┌───────────────────────────────────────┼───────────────────────────────────────┐
              ▼                                       ▼                                       ▼
  ┌───────────────────────┐               ┌───────────────────────┐               ┌───────────────────────┐
  │   AI Copilots         │               │ Autonomous Platform   │               │ Knowledge & Security  │
  │ • Pair Programmer     │               │ • Goal Orchestrator   │               │ • Security Scanner    │
  │ • Code Review         │               │ • Planner & Executor  │               │ • Quality Intelligence│
  │ • Debugging           │               │ • Verifier & Healing  │               │ • Release Readiness   │
  │ • Test & Doc Gen      │               │ • Approval Manager    │               │ • CI/CD Intelligence  │
  └───────────┬───────────┘               └───────────┬───────────┘               └───────────┬───────────┘
              │                                       │                                       │
              └───────────────────────────────────────┼───────────────────────────────────────┘
                                                      │
                                                      ▼
                               ┌───────────────────────────────────────────────┐
                               │           Retrieval & Graph Engine            │
                               │  (BM25 + FAISS Vector + Neo4j/SQLite Graph)   │
                               └──────────────────────┬────────────────────────┘
                                                      │
                                                      ▼
                               ┌───────────────────────────────────────────────┐
                               │            Local Model Gateway                │
                               │        (Ollama / Local LLM Inference)         │
                               └───────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required |
| [Ollama](https://ollama.com/download) | Latest | For local LLM + embeddings |

### 2. Pull Required Ollama Models

```bash
# Embedding model (required for indexing)
ollama pull nomic-embed-text

# LLM model (required for Q&A and AI Copilots)
ollama pull qwen2.5-coder:3b
```

### 3. Installation

```bash
# Clone the repository
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ecip-lite

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### 4. Run the API Server & Interactive Dashboard

```bash
python run_api.py
```

The server starts at `http://localhost:8000`.

- 📊 **Interactive Knowledge Dashboard**: Open `http://localhost:8000/dashboard/ui` in your browser.
- 📖 **Interactive Swagger API Docs**: Open `http://localhost:8000/docs` in your browser.

---

## 🌐 Key REST API Endpoints

```bash
# Index a local codebase
POST /api/v1/index
{
  "project_path": "projects/my-spring-boot-app"
}

# Ask AI Pair Programmer
POST /api/v1/query
{
  "question": "What REST endpoints are exposed by UserController?"
}

# Run System Diagnostics
GET /api/v1/diagnostics

# Access Interactive Dashboard UI
GET /dashboard/ui
```

---

## 🏆 100-Prompt Enterprise Milestone

ECIP Enterprise was constructed across a structured 100-Prompt Implementation Playbook:

- **Prompts 001–040**: AST Parsing, Method-Level Chunking, SQLite Metadata, FAISS Vector Store, Hybrid Search, Citation Engine, CLI, FastAPI.
- **Prompts 041–050**: Post-Release Maintenance, Governance, Enterprise Architecture & Knowledge Graph Specifications.
- **Prompts 051–065**: Neo4j Graph Provider, BM25 Hybrid Retrieval, Cross-Encoder Reranker, Call Graph Analyzer, RBAC, Multi-Tenancy, Audit Logging, Monitoring.
- **Prompts 066–075**: Backup & Recovery, Job Scheduler, Distributed Workers, Model Gateway, Plugin SDK, Marketplace, Analytics, Knowledge Dashboard (`/dashboard/ui`), Team Workspaces.
- **Prompts 076–082**: Event System, Semantic Caching, Agent Memory, Autonomous Planner & Executor, Self-Healing Engine, Knowledge Graph Reasoning.
- **Prompts 083–090**: Cross-Repo Reasoning, Architecture Advisor, Code Modernization, Refactoring Automation, Continuous Quality, CI/CD Intelligence, Security Intelligence, Release Readiness.
- **Prompts 091–100**: AI Pair Programmer, Code Review Assistant, Debugging Assistant, Test Generator, Docs Assistant, Architecture Copilot, DevOps Copilot, Operations Center, Autonomous Platform, and v1.0 Production Release.

---

## 🧪 Testing & Verification

Run full test suite across 532 passing unit & integration tests:

```bash
.venv/bin/python -m pytest tests/ -v
```

---

## 📄 License & Author

- **License**: Licensed under the [MIT License](LICENSE).
- **Author**: **Samir Zade** ([GitHub](https://github.com/Zade-Samir) | [LinkedIn](https://www.linkedin.com/in/samir-zade/))

---

> ⭐ If ECIP helps your team, give it a star on GitHub!
