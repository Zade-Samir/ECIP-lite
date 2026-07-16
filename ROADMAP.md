# ECIP Lite - Product Roadmap & Future Strategy

Welcome to the official roadmap for ECIP Lite. This document outlines the release history, current state, and near-term to long-term plans for the project.

## Current Status: v1.0.0 (Released)
ECIP Lite v1.0.0 establishes the core Local Retrieval-Augmented Generation (RAG) platform, including Java parsing, SQLite relationship graphs, FAISS vector indexing, and local inference integrations.

---

## v1.1.0 Roadmap (Planned)
The focus of the v1.1.0 release is to improve search quality, enhance performance, expand language support, and polish the developer experience.

### Key Objectives & Candidate Features
1. **Hybrid Search Integration**
   - Combine semantic search (FAISS) with keyword-based search (BM25) to improve query precision for exact code symbols.
2. **Enhanced Retrieval & Reranking**
   - Implement a lightweight local reranking stage (e.g., using Cohere or a local Cross-Encoder model).
3. **Cross-File Reasoning**
   - Enable the context builder to trace dependencies across multiple Java files to provide broader code context.
4. **Kotlin Language Support**
   - Extend the AST parser and chunker to support Kotlin `.kt` files.
5. **Markdown Export**
   - Allow exporting retrieved code context and query responses directly to Markdown files.
6. **Polished CLI UX**
   - Add interactive prompt modes, autocomplete, and enhanced progress bars for indexing.
7. **Performance & Memory Optimization**
   - Reduce RAM usage during large codebase indexing and improve indexing throughput.

---

## Maintenance & Versioning Policy

### Versioning Strategy
ECIP Lite adheres to **Semantic Versioning (SemVer) 2.0.0**:
- **Major (X.y.z):** Significant architectural changes or API-breaking changes.
- **Minor (x.Y.z):** New features, language support, or enhancements without breaking existing APIs.
- **Patch (x.y.Z):** Bug fixes, security patches, and documentation updates.

### Bug Triage Workflow
Issues submitted via GitHub are triaged according to the following process:
1. **Reproduce:** Verify the issue with a reproducible script or sample repository.
2. **Label Severity:** Classify as `critical`, `high`, `medium`, or `low`.
3. **Assign Owner:** Assign a maintainer or community contributor.
4. **Regression Test:** Create an integration or unit test that fails due to the bug.
5. **Implement Fix:** Code the fix on a dedicated bugfix branch.
6. **Review & Merge:** Review the PR against coding standards and merge to the main branch.
7. **Patch Release:** Trigger a patch release if the severity is high or critical.
8. **Update Changelog:** Update `CHANGELOG.md` with the bug description and contributor credit.
