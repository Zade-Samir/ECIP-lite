# Contributing to ECIP Lite

Thank you for your interest in contributing to ECIP Lite! 🎉

This document outlines the contribution process, coding standards, and guidelines to keep the project consistent and maintainable.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Branch Naming](#branch-naming)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)
- [Architecture Guidelines](#architecture-guidelines)

---

## Code of Conduct

Be respectful, collaborative, and constructive. All contributors are expected to maintain a welcoming environment for everyone, regardless of experience level.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/ECIP-lite.git
   cd ecip-lite
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/Zade-Samir/ECIP-lite.git
   ```

---

## Development Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) with `nomic-embed-text` and a chat LLM pulled

### Steps

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate     # macOS/Linux
# .venv\Scripts\activate      # Windows

# Install all dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your Ollama URL and model names

# Run the test suite to verify setup
python scripts/run_release_validation.py
```

---

## How to Contribute

### Report a Bug

Open a GitHub Issue with:
- Clear reproduction steps
- Expected vs actual behavior
- Python version, OS, Ollama version

### Request a Feature

Open a GitHub Issue with:
- Problem statement (what are you trying to do?)
- Proposed solution
- Alternatives considered

### Submit a Fix or Feature

1. Create a branch (see [Branch Naming](#branch-naming))
2. Make your changes
3. Write or update tests
4. Run the full validation suite
5. Open a Pull Request

---

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<short-description>` | `feat/python-parser` |
| Bug fix | `fix/<short-description>` | `fix/faiss-save-on-empty` |
| Documentation | `docs/<short-description>` | `docs/deployment-guide` |
| Release | `release/vX.Y.Z` | `release/v1.1.0` |
| Hotfix | `hotfix/<short-description>` | `hotfix/connection-leak` |

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code restructure without behavior change |
| `perf` | Performance improvement |
| `chore` | Build, CI, dependency updates |
| `release` | Version release preparation |

### Examples

```bash
feat(parser): add support for interface parsing
fix(faiss): call save() after batch embedding
docs(readme): update installation instructions
test(e2e): add cache hit/miss verification
release: prepare ECIP Lite v1.1.0
```

---

## Pull Request Process

1. **Title** should follow the commit message convention
2. **Description** must include:
   - What changed and why
   - How to test the change
   - Screenshots or logs for UI/output changes
3. **All tests must pass** before requesting review
4. **One reviewer approval** is required to merge
5. **Squash merge** is used — keep your PR focused

### PR Checklist

- [ ] Tests written and passing
- [ ] `python scripts/run_release_validation.py` passes
- [ ] Docstrings updated for changed functions
- [ ] `CHANGELOG.md` updated (for features/fixes)
- [ ] No debug print statements left in code

---

## Testing Requirements

Every contribution **must** include tests:

- **Unit tests** for all new service methods (`tests/test_*.py`)
- **Integration tests** if touching the database or vector store
- **E2E tests** if changing the full query pipeline

Run tests:

```bash
# All tests (recommended before PR)
python scripts/run_release_validation.py

# Specific module
python -m unittest tests/test_parser.py -v
python -m unittest tests/e2e/test_e2e_pipeline.py -v
```

**Minimum coverage expectation:** All new public methods must have at least one test.

---

## Code Style

- **Python 3.10+ type hints** on all function signatures
- **Docstrings** on all public classes and methods (Google style)
- **No bare `except`** — catch specific exceptions
- **Logging over print** — use `get_logger(__name__)` from `ecip_core.logging`
- **No hardcoded paths** — use `settings.*` for all configurable values

### Module Structure

When adding a new subsystem, follow the existing pattern:

```
ecip_core/<subsystem>/
    __init__.py
    <main_service>.py    ← Primary service class
    models.py            ← Domain models (Pydantic)
```

---

## Architecture Guidelines

- **Do not modify** parser, chunking, or embedding logic when adding retrieval features — inject via the coordinator
- **Cache at the service boundary** — use `cache_manager.cached()` decorator, not inside business logic
- **Diagnostics check** for any new stateful resource you add (new file, DB table, index)
- **Metrics timer** for any operation that could be a performance bottleneck

---

## Areas Open for Contribution

| Area | Complexity | Description |
|------|-----------|-------------|
| 🐍 Python parser | High | Add Python AST parsing support |
| 🌐 Web UI | High | Browser-based query interface |
| 🔌 New embedding providers | Medium | OpenAI, LM Studio, llama.cpp |
| 📊 Dependency visualization | Medium | Graph rendering in the CLI or UI |
| 🌍 Multi-language chunking | Medium | Language-agnostic chunking strategy |
| 🔒 Auth middleware | Low | API key validation for REST endpoints |
| 🧪 More test fixtures | Low | Richer sample Java projects for testing |

---

Thank you for contributing to ECIP Lite! 🚀
