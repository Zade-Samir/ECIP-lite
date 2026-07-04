# ECIP Lite 🚀

**ECIP Lite (Enterprise Code Intelligence Platform Lite)** is a secure, local-first code intelligence and analysis assistant. It enables developers to index codebases and perform queries against them while maintaining complete data privacy by running language models locally.

---

## ✨ Features

- **Local & Secure:** Runs entirely on-premise or locally. No external APIs, third-party data transmission, or cloud dependencies.
- **Codebase Indexing:** Extracts high-level structural metadata from source code (e.g., classes, methods, packages).
- **Interactive Query Engine:** Integrates local LLMs with codebase context to answer technical questions and analyze project architecture.
- **Configurable LLM Pipeline:** Supports custom model endpoints, temperature adjustments, and customizable system prompts.

---

## 🛠️ Prerequisites

1. **Python:** Version 3.10 or higher.
2. **Ollama:** Installed and running locally.
   - Recommended model: `qwen3.5:9b` or any compatible code model.
   - Run the model: `ollama run qwen3.5:9b`

---

## 🚀 Getting Started

### 1. Installation

Clone the repository and install the required dependencies:

```bash
# Navigate to the project directory
cd ecip-lite

# Create and activate a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create or modify the `.env` file in the root directory to customize model configurations:

```env
# URL where your local Ollama instance is running
OLLAMA_BASE_URL=http://localhost:11434

# Model to use for inference
MODEL_NAME=qwen3.5:9b

# Generation settings
TEMPERATURE=0.2
TOP_P=0.9
MAX_TOKENS=4096
STREAM=false

# System persona/prompt
SYSTEM_PROMPT="You are ECIP, an expert Java and Spring Boot Architect."
```

### 3. Running the Assistant

Run the interactive command-line interface to start asking questions:

```bash
python -m ecip_core.main
```

Type your questions inside the prompt, and type `exit` or `quit` to close the session.
