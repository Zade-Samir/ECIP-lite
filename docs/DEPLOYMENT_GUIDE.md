# ECIP Lite — Deployment Guide

**Version:** v1.0.0  
**Audience:** Developers deploying ECIP Lite on a local machine or team server

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Local Development Deployment](#local-development-deployment)
3. [Team Server Deployment](#team-server-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Starting Services](#starting-services)
6. [Verifying the Deployment](#verifying-the-deployment)
7. [Logs](#logs)
8. [Upgrading](#upgrading)

---

## System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Python | 3.10 | 3.12 |
| RAM | 4 GB | 8+ GB |
| Disk | 2 GB | 10+ GB (for large FAISS indexes) |
| CPU | Any | Apple Silicon / modern x86-64 |
| OS | macOS / Linux | macOS / Ubuntu 22.04+ |

> **Windows:** Supported via WSL2 (Windows Subsystem for Linux). Native Windows is not tested.

### Ollama

[Install Ollama](https://ollama.com/download) and pull the required models:

```bash
ollama pull nomic-embed-text   # embedding model
ollama pull qwen2.5-coder:3b         # or any chat model you prefer
```

Ollama must be running before starting ECIP Lite.

---

## Local Development Deployment

```bash
# 1. Clone
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ecip-lite

# 2. Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
# Edit .env as needed

# 5. Run validation suite to confirm setup
python scripts/run_release_validation.py

# 6. Start CLI
python -m ecip_core.main

# 6b. OR start REST API
python run_api.py
```

---

## Team Server Deployment

For a shared deployment where your team queries a central ECIP Lite instance:

```bash
# 1. Clone on the server
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ecip-lite

# 2. Create venv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
# Set OLLAMA_BASE_URL to the server where Ollama runs
# Set ECIP_PROFILE=production

# 4. Mount your Java project
cp -r /path/to/project projects/myproject

# 5. Index the project (one-time)
python -m ecip_core.main
# Let it complete, then exit

# 6. Start the API server
# Option A: Direct (development)
python run_api.py

# Option B: Background with nohup (simple production)
nohup python run_api.py > logs/api.log 2>&1 &
```

### Expose to Team (Simple)

If running on a LAN server, change the Uvicorn bind:

```bash
# In run_api.py — already bound to 0.0.0.0:8000
# Team members access via: http://<server-ip>:8000
```

> **Note:** ECIP Lite has no authentication in v1.0. For internal team use only. Do not expose publicly.

---

## Environment Configuration

All configuration is in `.env`. Key production settings:

```env
# Use your team Ollama server
OLLAMA_BASE_URL=http://ollama-server:11434

# Production profile
ECIP_PROFILE=production

# Enable caching (reduces repeated embedding costs)
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# Log to file
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/ecip.log
```

### Profile Differences

| Setting | `development` | `testing` | `production` |
|---------|-------------|---------|------------|
| Log level | `DEBUG` | `WARNING` | `INFO` |
| Cache | Enabled | Disabled | Enabled |
| Reload | Yes | No | No |

---

## Starting Services

### CLI

```bash
source .venv/bin/activate
python -m ecip_core.main
```

### REST API

```bash
source .venv/bin/activate
python run_api.py
# → Running on http://0.0.0.0:8000
# → Docs: http://localhost:8000/docs
```

### Run Indexer Only (no CLI loop)

You can trigger indexing directly via the API after starting it:

```bash
curl -X POST http://localhost:8000/api/v1/index \
  -H "Content-Type: application/json" \
  -d '{"project_path": "projects/myproject"}'
```

---

## Verifying the Deployment

### 1. Run the validation suite

```bash
python scripts/run_release_validation.py
```

Expected output:

```
Overall Status:   PASSED
Total Tests Run:  255
Passed:           255 ✅
```

### 2. Check the API health endpoint

```bash
curl http://localhost:8000/api/v1/diagnostics
```

Expected: `"overall_status": "healthy"`

### 3. Test a query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What classes are in this project?"}'
```

---

## Logs

Log files are written to `logs/ecip.log` (if `LOG_FILE_PATH` is configured).

```bash
# Watch live logs
tail -f logs/ecip.log

# Filter errors only
grep "ERROR" logs/ecip.log
```

Log format:

```
[2026-07-09 01:12:53] INFO | ecip_core.indexing.index_builder | CID:abc123 | Index started
[2026-07-09 01:12:53] INFO | ecip_core.indexing.index_builder | CID:abc123 | Found 42 Java files
```

---

## Upgrading

```bash
# Pull latest changes
git pull origin main

# Reinstall dependencies (if requirements.txt changed)
pip install -r requirements.txt

# Re-run validation suite
python scripts/run_release_validation.py

# Re-start services
python run_api.py
```

> **FAISS index compatibility:** If the embedding model changes between versions, you must delete `.ecip/` and re-index.

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `Connection refused` on Ollama | Ollama not running | Run `ollama serve` |
| `FAISS index not found` | First run before indexing | Run indexer first |
| Slow first query | Cold FAISS load | Expected — subsequent queries are fast |
| `degraded` diagnostics | Vector count mismatch | Delete `.ecip/` and re-index |
| Empty search results | No project indexed | Run indexer against your project path |
