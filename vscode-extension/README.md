# ECIP Lite — VS Code Extension

This is the VS Code extension for **ECIP Lite (Enterprise Code Intelligence Platform Lite)**, bringing local, privacy-first, on-premise AI chat assistant capability directly to your editor.

## Features

- ⚡ **Zero-Config Folder Indexing**: Index your active workspace folder in the daemon directly from the extension view.
- 📂 **Multi-Project Workspace Context**: Easily switch between indexed projects.
- 💬 **Interactive AI Chat**: Ask questions about your code (powered offline by local Ollama models like Qwen 2.5 Coder).
- 🔗 **Clickable Citations & References**: Instantly jump to the referenced files, classes, methods, and line ranges inside VS Code by clicking on response citation badges.

---

## Getting Started & Debugging

### Prerequisites
1. **Node.js & npm** (Node 18+ recommended)
2. **ECIP Lite Daemon Running**: Ensure your local FastAPI service is running:
   ```bash
   python run_api.py
   ```
   Verify it's reachable at `http://127.0.0.1:8000/health`.

### Installation & Launching
1. Open the `vscode-extension` folder in VS Code.
2. Open a terminal inside the extension folder and install dependencies:
   ```bash
   npm install
   ```
3. Compile the TypeScript code (if you make changes, it watches and compiles automatically):
   ```bash
   npm run compile
   ```
4. Press **`F5`** on your keyboard (or click **Run and Debug** -> **Run Extension** in the sidebar).
5. A new window named **[Extension Development Host]** will launch.
6. Look at the left sidebar (Activity Bar) in the new window. You will see the **ECIP Lite** icon.
7. Open the tab, click **Index Folder** to scan your active project workspace, and start chatting offline!
