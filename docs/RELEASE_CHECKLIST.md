# ECIP Lite Release Validation Checklist

This document details the checklist and automated gating suite required before releasing any new version of ECIP Lite.

## 1. Automated Release Gating

Before any release candidate is promoted, the automated release validation script must run successfully.

Run the gating suite:
```bash
python scripts/run_release_validation.py
```

This validation script:
- Automatically discovers and executes all unit, integration, and E2E tests in the workspace.
- Measures execution time and tracks success rates.
- Generates a human-readable terminal report.
- Saves a machine-readable JSON health report to `release_validation_report.json`.
- Exits with exit code `0` on success, and a non-zero status on any test failure.

## 2. Core Checklist

### A. Environment Configuration
- [ ] Active profile configurations (`development`, `testing`, `production`) load default values without throwing exceptions.
- [ ] No local configuration variables (IPs, hardcoded file paths) are committed to standard code files.
- [ ] Backward compatibility layer in `settings.py` correctly redirects legacy calls to unified configuration settings.

### B. Workspace Isolation
- [ ] Running tests does not corrupt the default master database `data/ecip.db`.
- [ ] Project-specific files (`data/ecip_{project_id}.db` and `.ecip/faiss_{project_id}.index`) are cleaned and purged completely upon workspace deletion.
- [ ] Cache keys namespaces isolate results between distinct active workspaces.

### C. Performance & Diagnostics
- [ ] Diagnostics suite runs checks successfully and reports status `healthy` on clean indexes.
- [ ] Diagnostics reports warnings (such as vector counts mismatches or missing file pointers) instead of crashing on degraded project states.
- [ ] Continuous timing metrics are enabled and aggregate profiling without significant latency overhead.

---

*Verified for release gating readiness. Ready to ship.*
