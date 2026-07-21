import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'ecip-lite-chat-view';
    private _view?: vscode.WebviewView;
    private _chatHistory: Map<string, Array<{ role: 'user' | 'assistant'; content: string }>> = new Map();

    private _selectedModel: string | undefined;

    constructor(private readonly _context: vscode.ExtensionContext) {
        this._selectedModel = this._context.globalState.get<string>('selectedModel');
    }

    private get _extensionUri(): vscode.Uri {
        return this._context.extensionUri;
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        // Handle messages from the Webview UI
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'getWorkspaces': {
                    await this.fetchWorkspaces();
                    break;
                }
                case 'getModels': {
                    await this.fetchModelsList();
                    break;
                }
                case 'indexCurrentWorkspace': {
                    await this.indexCurrentWorkspace();
                    break;
                }
                case 'askQuestion': {
                    await this.handleQuery(data.projectId, data.question);
                    break;
                }
                case 'modelChanged': {
                    this._selectedModel = data.model;
                    this._context.globalState.update('selectedModel', data.model);
                    break;
                }
                case 'openFile': {
                    await this.openFileAtLine(data.filePath, data.startLine, data.endLine);
                    break;
                }
                case 'showWarning': {
                    vscode.window.showWarningMessage(data.message);
                    break;
                }
                case 'showInfo': {
                    vscode.window.showInformationMessage(data.message);
                    break;
                }
                case 'selectProject': {
                    const history = this._chatHistory.get(data.projectId) || [];
                    this._view?.webview.postMessage({
                        type: 'restoreHistory',
                        history: history
                    });
                    break;
                }
            }
        });

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Proactive fetches fallback
        this.fetchWorkspaces();
        this.fetchModelsList();
    }

    private getApiUrl(): string {
        const config = vscode.workspace.getConfiguration('ecipLite');
        let url = config.get<string>('apiUrl') || 'http://127.0.0.1:8000';
        if (url.endsWith('/')) {
            url = url.slice(0, -1);
        }
        return url;
    }

    private async fetchWorkspaces() {
        try {
            const response = await fetch(`${this.getApiUrl()}/api/v1/workspaces`);
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            const data: any = await response.json();
            this._view?.webview.postMessage({
                type: 'workspacesList',
                workspaces: data.workspaces || [],
                active: data.active || null
            });
        } catch (err) {
            this._view?.webview.postMessage({
                type: 'backendError',
                message: 'Failed to connect to ECIP Lite daemon. Make sure uvicorn is running on port 8000.'
            });
        }
    }

    private async fetchModelsList() {
        try {
            const response = await fetch(`${this.getApiUrl()}/api/v1/query/models`);
            if (response.ok) {
                const data: any = await response.json();
                vscode.window.showInformationMessage(`Models fetched: ${JSON.stringify(data.models)}`);
                this._view?.webview.postMessage({
                    type: 'modelsList',
                    models: data.models || [],
                    selected: this._selectedModel || (data.models && data.models[0]) || ''
                });
                if (!this._selectedModel && data.models && data.models.length > 0) {
                    this._selectedModel = data.models[0];
                    this._context.globalState.update('selectedModel', this._selectedModel);
                }
            } else {
                vscode.window.showErrorMessage(`Models response not OK: ${response.status}`);
            }
        } catch (err: any) {
            vscode.window.showErrorMessage(`Fetch models error: ${err.message || err}`);
            this._view?.webview.postMessage({
                type: 'modelsList',
                models: [],
                selected: this._selectedModel || ''
            });
        }
    }

    private async indexCurrentWorkspace() {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders || folders.length === 0) {
            vscode.window.showErrorMessage('No workspace folder open in VS Code to index.');
            return;
        }

        const projectPath = folders[0].uri.fsPath;
        const projectAlias = folders[0].name;

        // Notify user indexing started
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `ECIP Lite: Indexing ${projectAlias}...`,
            cancellable: false
        }, async (progress) => {
            try {
                // First, register workspace
                const regResponse = await fetch(`${this.getApiUrl()}/api/v1/workspaces`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project_id: projectAlias,
                        alias: projectAlias,
                        root_path: projectPath
                    })
                });

                if (!regResponse.ok && regResponse.status !== 409 && regResponse.status !== 500) {
                    throw new Error('Failed to register workspace.');
                }

                // Trigger indexing
                const indexResponse = await fetch(`${this.getApiUrl()}/api/v1/index`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project_path: projectPath,
                        project_alias: projectAlias
                    })
                });

                if (!indexResponse.ok) {
                    const errorDetails = await indexResponse.text();
                    throw new Error(`Indexing failed: ${errorDetails}`);
                }

                vscode.window.showInformationMessage(`Successfully indexed project: ${projectAlias}`);
                await this.fetchWorkspaces();
            } catch (err: any) {
                vscode.window.showErrorMessage(`Indexing error: ${err.message}`);
            }
        });
    }

    private async handleQuery(projectId: string, question: string) {
        if (!projectId) {
            this._view?.webview.postMessage({
                type: 'queryResponse',
                error: 'Please select or index a workspace project first.'
            });
            return;
        }

        // Retrieve and update history
        if (!this._chatHistory.has(projectId)) {
            this._chatHistory.set(projectId, []);
        }
        const projectHistory = this._chatHistory.get(projectId)!;
        projectHistory.push({ role: 'user', content: question });

        // Retrieve sliding window (last 6 messages) to send
        const apiHistory = projectHistory.slice(-6);

        try {
            const response = await fetch(`${this.getApiUrl()}/api/v1/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    question: question,
                    stream: true,
                    history: apiHistory,
                    model: this._selectedModel
                })
            });

            if (!response.ok) {
                const errText = await response.text();
                let detail = `Server responded with ${response.status}`;
                try {
                    const parsed = JSON.parse(errText);
                    detail = parsed.detail || detail;
                } catch {}
                throw new Error(detail);
            }

            if (!response.body) {
                throw new Error("No response body received from API.");
            }

            const decoder = new TextDecoder("utf-8");
            let buffer = "";
            const reader = (response.body as any);
            let accumulatedAnswer = "";

            for await (const chunk of reader) {
                buffer += decoder.decode(chunk, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.trim()) {
                        continue;
                    }
                    try {
                        const parsed = JSON.parse(line);
                        if (parsed.type === "token") {
                            accumulatedAnswer += parsed.text;
                            this._view?.webview.postMessage({
                                type: 'queryToken',
                                text: parsed.text
                            });
                        } else if (parsed.type === "done") {
                            projectHistory.push({ role: 'assistant', content: accumulatedAnswer });
                            this._view?.webview.postMessage({
                                type: 'queryResponse',
                                citations: parsed.citations || [],
                                modelName: parsed.model_name || 'local-llm',
                                durationMs: parsed.duration_ms || 0
                            });
                        } else if (parsed.type === "error") {
                            this._view?.webview.postMessage({
                                type: 'queryResponse',
                                error: parsed.message
                            });
                        }
                    } catch (e) {
                        // ignore malformed JSON
                    }
                }
            }
        } catch (err: any) {
            this._view?.webview.postMessage({
                type: 'queryResponse',
                error: err.message || 'Error occurred while querying daemon.'
            });
        }
    }

    private async openFileAtLine(filePath: string, startLine: number, endLine: number) {
        try {
            const uri = vscode.Uri.file(filePath);
            const doc = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(doc);
            
            if (startLine > 0) {
                const startPos = new vscode.Position(startLine - 1, 0);
                const endPos = new vscode.Position((endLine || startLine) - 1, 999);
                editor.selection = new vscode.Selection(startPos, endPos);
                editor.revealRange(new vscode.Range(startPos, endPos), vscode.TextEditorRevealType.InCenter);
            }
        } catch (err: any) {
            vscode.window.showErrorMessage(`Could not open file: ${err.message}`);
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ECIP Lite Chat</title>
    <style>
        :root {
            --bg-color: #000000;
            --card-bg: #333333;
            --border-color: #555555;
            --accent-color: #3b82f6;
            --accent-hover: #2563eb;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 12px;
            display: flex;
            flex-direction: column;
            height: 100vh;
            box-sizing: border-box;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }

        .header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background: linear-gradient(to right, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .project-selector {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 8px;
            border-radius: 6px;
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .project-selector label {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .select-row {
            display: flex;
            gap: 6px;
        }

        select {
            flex-grow: 1;
            background: #333333;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 6px;
            border-radius: 4px;
            font-size: 12px;
            outline: none;
        }

        button.btn-icon {
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 6px 8px;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }

        button.btn-icon:hover {
            color: var(--text-primary);
            border-color: var(--text-secondary);
            background-color: rgba(255, 255, 255, 0.05);
        }

        button.btn-primary {
            background-color: var(--accent-color);
            border: none;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        button.btn-primary:hover {
            background-color: var(--accent-hover);
        }

        .chat-area {
            flex-grow: 1;
            overflow-y: auto;
            background-color: transparent;
            padding: 10px 4px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-bottom: 12px;
        }

        .message {
            max-width: 90%;
            padding: 8px 12px;
            font-size: 13px;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .message.user {
            background-color: #222222;
            color: #ffffff;
            align-self: flex-end;
            border-radius: 18px;
            border: 1px solid #444444;
            padding: 10px 16px;
            margin-left: 20%;
        }

        .message.assistant {
            background-color: transparent !important;
            color: #e2e8f0;
            align-self: flex-start;
            border: none !important;
            padding: 0;
            max-width: 100%;
        }

        .message.assistant h1,
        .message.assistant h2,
        .message.assistant h3 {
            color: #ffffff;
            margin-top: 18px;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .message.assistant h1 { font-size: 18px; }
        .message.assistant h2 { font-size: 16px; }
        .message.assistant h3 { font-size: 14px; }

        .message.assistant ul {
            margin: 8px 0 12px 18px;
            padding: 0;
            list-style-type: disc;
        }

        .message.assistant li {
            margin-bottom: 6px;
            color: #cbd5e1;
            line-height: 1.5;
        }

        .text-line {
            margin-bottom: 8px;
            line-height: 1.5;
            color: #e2e8f0;
        }

        .message.error {
            background-color: rgba(239, 68, 68, 0.1);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
            align-self: center;
            max-width: 100%;
            border-radius: 8px;
            padding: 8px 12px;
        }

        .message code {
            background-color: #222222;
            color: #e2e8f0;
            padding: 2px 5px;
            border-radius: 4px;
            font-family: Menlo, Monaco, Consolas, "Courier New", monospace;
            font-size: 12px;
            border: 1px solid #444444;
        }

        /* Code block container */
        .code-block-container {
            background-color: #111111;
            border: 1px solid #333333;
            border-radius: 8px;
            margin: 12px 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .code-block-header {
            background-color: #1c1c1c;
            border-bottom: 1px solid #2d2d2d;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 12px;
            font-size: 11px;
            color: #94a3b8;
        }

        .code-block-lang {
            font-family: Menlo, Monaco, Consolas, monospace;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            color: #cbd5e1;
        }

        .code-icon {
            color: #64748b;
        }

        button.btn-copy {
            background: none;
            border: 1px solid #334155;
            color: #94a3b8;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 10px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
        }

        button.btn-copy:hover {
            color: #ffffff;
            background-color: #2d2d2d;
            border-color: #475569;
        }

        .code-block-container pre {
            background: none !important;
            border: none !important;
            margin: 0 !important;
            padding: 10px 12px !important;
            overflow-x: auto;
        }

        .code-block-container pre code {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #cbd5e1;
            font-family: Menlo, Monaco, Consolas, "Courier New", monospace;
            font-size: 12px;
            line-height: 1.5;
            display: block;
        }

        .citations-container {
            margin-top: 8px;
            border-top: 1px dashed var(--border-color);
            padding-top: 6px;
        }

        .citations-title {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 4px;
        }

        .citation-badge {
            display: inline-flex;
            align-items: center;
            background-color: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
            margin-right: 4px;
            margin-bottom: 4px;
            transition: all 0.2s;
        }

        .citation-badge:hover {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }

        .metadata-footer {
            font-size: 10px;
            color: var(--text-muted);
            margin-top: 6px;
            display: flex;
            justify-content: space-between;
        }

        .input-container {
            background-color: #1a1a1a;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 8px 10px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: auto;
            box-sizing: border-box;
        }

        textarea {
            width: 100%;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 13px;
            outline: none;
            resize: none;
            height: 48px;
            font-family: inherit;
            box-sizing: border-box;
        }

        .input-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .left-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .model-select-wrapper {
            position: relative;
            display: flex;
            align-items: center;
            background: #2b2b2b;
            border-radius: 18px;
            padding: 4px 10px;
            border: 1px solid #444444;
            color: var(--text-secondary);
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .model-select-wrapper span {
            margin-right: 4px;
            pointer-events: none;
            user-select: none;
        }

        .model-select-wrapper select {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }

        .model-select-wrapper:hover {
            background: #3a3a3a;
            color: var(--text-primary);
        }

        button.btn-send {
            background-color: #3b82f6;
            border: none;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.2s;
            flex-shrink: 0;
        }

        button.btn-send:hover {
            background-color: #2563eb;
        }

        .loading-dots {
            display: inline-flex;
            gap: 4px;
            align-items: center;
            height: 12px;
        }

        .dot {
            width: 6px;
            height: 6px;
            background-color: var(--text-secondary);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
        }

        .reasoning-container {
            background-color: #121212;
            border: 1px solid #333333;
            border-radius: 6px;
            margin-bottom: 8px;
            overflow: hidden;
            font-size: 12px;
            text-align: left;
        }

        .reasoning-summary {
            padding: 8px 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
            background-color: #1a1a1a;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .reasoning-summary:hover {
            background-color: #222222;
            color: var(--text-primary);
        }

        .reasoning-header-left {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .reasoning-chevron {
            font-size: 10px;
            transition: transform 0.2s ease;
        }

        .reasoning-container[open] .reasoning-chevron {
            transform: rotate(90deg);
        }

        .reasoning-content {
            padding: 10px;
            border-top: 1px solid #333333;
            color: #94a3b8;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: var(--vscode-editor-font-family, Consolas, Monaco, monospace);
            font-size: 11px;
            line-height: 1.4;
            background-color: #0d0d0d;
        }

        .reasoning-loader {
            width: 8px;
            height: 8px;
            border: 1.5px solid #94a3b8;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h3>ECIP Lite Code Intelligence</h3>
        <button class="btn-icon" id="btn-refresh" title="Refresh Workspaces">🔄</button>
    </div>

    <div class="project-selector">
        <label for="project-select">ACTIVE WORKSPACE PROJECT</label>
        <div class="select-row">
            <select id="project-select">
                <option value="">Loading workspaces...</option>
            </select>
            <button class="btn-primary" id="btn-index-curr" title="Register & Index active directory in VS Code">⚡ Index Folder</button>
        </div>
        <div style="margin-top: 6px; display: flex; align-items: center;">
            <span id="index-status-badge" style="display: none; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;">Status: Unknown</span>
        </div>
    </div>

    <div class="chat-area" id="chat-area">
        <div class="message assistant">
            Hello! Select an indexed project workspace and ask me questions about your Java/Spring Boot code. Click <b>⚡ Index Folder</b> to scan your current directory.
        </div>
    </div>

    <div class="input-container">
        <textarea id="question-input" placeholder="Ask a question about the code..."></textarea>
        <div class="input-actions">
            <div class="left-actions">
                <div class="model-select-wrapper" title="Select Local LLM Model">
                    <span>+</span>
                    <span id="selected-model-label">Loading...</span>
                    <span>▾</span>
                    <select id="model-select">
                        <option value="">Loading...</option>
                    </select>
                </div>
            </div>
            <button class="btn-send" id="btn-send" title="Send question">
                <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        window.onerror = function(msg, url, line, col, error) {
            vscode.postMessage({
                type: 'showWarning',
                message: 'Webview Error: ' + msg + ' (Line: ' + line + ')'
            });
            return false;
        };

        const select = document.getElementById('project-select');
        const refreshBtn = document.getElementById('btn-refresh');
        const indexCurrBtn = document.getElementById('btn-index-curr');
        const sendBtn = document.getElementById('btn-send');
        const input = document.getElementById('question-input');
        const chatArea = document.getElementById('chat-area');
        const modelSelect = document.getElementById('model-select');
        const selectedModelLabel = document.getElementById('selected-model-label');

        let currentWorkspaces = [];

        // Update status badge and restore history on selection change
        select.addEventListener('change', () => {
            updateStatusBadge();
            vscode.postMessage({
                type: 'selectProject',
                projectId: select.value
            });
        });

        let accumulatedAnswer = "";
        let accumulatedRaw = "";

        // Refresh action
        refreshBtn.addEventListener('click', () => {
            vscode.postMessage({ type: 'getWorkspaces' });
            vscode.postMessage({ type: 'getModels' });
        });

        // Pull initial configurations
        vscode.postMessage({ type: 'getWorkspaces' });
        vscode.postMessage({ type: 'getModels' });

        // Index current folder
        indexCurrBtn.addEventListener('click', () => {
            vscode.postMessage({ type: 'indexCurrentWorkspace' });
        });

        function updateStatusBadge() {
            const projectId = select.value;
            const project = currentWorkspaces.find(w => w.project_id === projectId);
            const badge = document.getElementById('index-status-badge');
            if (!badge) return;

            if (!project) {
                badge.style.display = 'none';
                return;
            }

            badge.style.display = 'inline-block';
            
            const isIndexed = (project.indexed_files && project.indexed_files > 0) || project.status === 'active';
            if (isIndexed) {
                badge.textContent = 'Status: Indexed (' + (project.indexed_files || 0) + ' files)';
                badge.style.backgroundColor = '#10b981'; // Green
                badge.style.color = '#ffffff';
            } else {
                badge.textContent = 'Status: Not Indexed';
                badge.style.backgroundColor = '#ef4444'; // Red
                badge.style.color = '#ffffff';
            }
        }

        // Trigger query on Send
        function submitQuery() {
            const question = input.value.trim();
            const projectId = select.value;

            if (!projectId) {
                vscode.postMessage({ type: 'showWarning', message: 'Please select a workspace project first.' });
                return;
            }

            if (!question) return;

            // Render user message
            renderMessage(question, 'user');
            input.value = '';

            // Render assistant placeholder for streaming
            accumulatedAnswer = "";
            accumulatedRaw = "";
            const activeMsgId = 'assistant-active';
            
            const oldActive = document.getElementById(activeMsgId);
            if (oldActive) oldActive.id = "";

            renderAssistantPlaceholder(activeMsgId);

            // Post request to extension core
            vscode.postMessage({
                type: 'askQuestion',
                projectId: projectId,
                question: question
            });
        }

        sendBtn.addEventListener('click', submitQuery);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitQuery();
            }
        });

        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'modelsList': {
                    updateModelDropdown(message.models, message.selected);
                    break;
                }
                case 'workspacesList': {
                    currentWorkspaces = message.workspaces || [];
                    updateProjectSelect(message.workspaces, message.active);
                    break;
                }
                case 'backendError': {
                    renderMessage(message.message, 'error');
                    break;
                }
                case 'queryToken': {
                    const activeBubble = document.getElementById('assistant-active');
                    if (activeBubble) {
                        const dots = activeBubble.querySelector('.loading-dots');
                        if (dots) dots.remove();

                        const rawToken = message.text;
                        accumulatedRaw += rawToken;

                        const thinkStartIdx = accumulatedRaw.indexOf('<think>');
                        const thinkEndIdx = accumulatedRaw.indexOf('</think>');

                        let displayAnswer = "";
                        let displayReasoning = "";
                        let isThinking = false;

                        if (thinkStartIdx !== -1) {
                            if (thinkEndIdx === -1) {
                                displayReasoning = accumulatedRaw.substring(thinkStartIdx + 7);
                                displayAnswer = accumulatedRaw.substring(0, thinkStartIdx);
                                isThinking = true;
                            } else {
                                displayReasoning = accumulatedRaw.substring(thinkStartIdx + 7, thinkEndIdx);
                                displayAnswer = accumulatedRaw.substring(0, thinkStartIdx) + accumulatedRaw.substring(thinkEndIdx + 8);
                            }
                        } else {
                            displayAnswer = accumulatedRaw;
                        }

                        let reasoningHtml = "";
                        if (displayReasoning || isThinking) {
                            const loaderHtml = isThinking ? '<span class="reasoning-loader"></span>' : '';
                            const titleText = isThinking ? 'Thinking...' : 'Thoughts & Reasoning';
                            reasoningHtml = 
                                '<details class="reasoning-container">' +
                                    '<summary class="reasoning-summary">' +
                                        '<div class="reasoning-header-left">' +
                                            '<span>💡</span>' +
                                            '<span>' + titleText + '</span> ' + loaderHtml +
                                        '</div>' +
                                        '<span class="reasoning-chevron">▶</span>' +
                                    '</summary>' +
                                    '<div class="reasoning-content">' + escapeHtml(displayReasoning) + '</div>' +
                                '</details>';
                        }

                        const contentSpan = activeBubble.querySelector('.content');
                        if (contentSpan) {
                            contentSpan.innerHTML = reasoningHtml + formatTextToHtml(displayAnswer);
                        }
                        scrollToBottom();
                    }
                    break;
                }
                case 'queryResponse': {
                    const activeBubble = document.getElementById('assistant-active');
                    if (activeBubble) {
                        const dots = activeBubble.querySelector('.loading-dots');
                        if (dots) dots.remove();

                        if (message.error) {
                            const contentSpan = activeBubble.querySelector('.content');
                            if (contentSpan) {
                                contentSpan.innerHTML = '<span style="color: #f87171;">' + message.error + '</span>';
                            }
                            activeBubble.className = 'message error';
                        } else {
                            // Extract finalized thoughts
                            const thinkStartIdx = accumulatedRaw.indexOf('<think>');
                            const thinkEndIdx = accumulatedRaw.indexOf('</think>');
                            let displayAnswer = "";
                            let displayReasoning = "";

                            if (thinkStartIdx !== -1) {
                                if (thinkEndIdx === -1) {
                                    displayReasoning = accumulatedRaw.substring(thinkStartIdx + 7);
                                    displayAnswer = accumulatedRaw.substring(0, thinkStartIdx);
                                } else {
                                    displayReasoning = accumulatedRaw.substring(thinkStartIdx + 7, thinkEndIdx);
                                    displayAnswer = accumulatedRaw.substring(0, thinkStartIdx) + accumulatedRaw.substring(thinkEndIdx + 8);
                                }
                            } else {
                                displayAnswer = accumulatedRaw;
                            }

                            let reasoningHtml = "";
                            if (displayReasoning) {
                                reasoningHtml = 
                                    '<details class="reasoning-container">' +
                                        '<summary class="reasoning-summary">' +
                                            '<div class="reasoning-header-left">' +
                                                '<span>💡</span>' +
                                                '<span>Thoughts & Reasoning</span>' +
                                            '</div>' +
                                            '<span class="reasoning-chevron">▶</span>' +
                                        '</summary>' +
                                        '<div class="reasoning-content">' + escapeHtml(displayReasoning) + '</div>' +
                                    '</details>';
                            }

                            // Inject citations/remembered context snippets
                            let contextHtml = "";
                            if (message.citations && message.citations.length > 0) {
                                let snippets = [];
                                message.citations.forEach((c, idx) => {
                                    if (c.content && c.content.trim()) {
                                        const fileBase = c.file_path.split('/').pop().split('\\').pop();
                                        snippets.push(
                                            '--- Reference [' + (idx + 1) + ']: ' + fileBase + ' ---\n' +
                                            c.content.trim()
                                        );
                                    }
                                });
                                if (snippets.length > 0) {
                                    contextHtml = 
                                        '<details class="reasoning-container" style="margin-top: 8px;">' +
                                            '<summary class="reasoning-summary">' +
                                                '<div class="reasoning-header-left">' +
                                                    '<span>📖</span>' +
                                                    '<span>Remembered Code Context</span>' +
                                                '</div>' +
                                                '<span class="reasoning-chevron">▶</span>' +
                                            '</summary>' +
                                            '<div class="reasoning-content" style="white-space: pre;">' + escapeHtml(snippets.join('\n\n')) + '</div>' +
                                        '</details>';
                                }
                            }

                            const contentSpan = activeBubble.querySelector('.content');
                            if (contentSpan) {
                                contentSpan.innerHTML = reasoningHtml + contextHtml + formatTextToHtml(displayAnswer);
                            }

                            renderAssistantMetadata(activeBubble, message);
                        }
                        activeBubble.id = "";
                    }
                    break;
                }
                case 'restoreHistory': {
                    // Clear chat area except the greeting
                    const greeting = chatArea.querySelector('.message.assistant:not([id])');
                    chatArea.innerHTML = '';
                    if (greeting && !greeting.querySelector('.citations-container') && !greeting.querySelector('.metadata-footer')) {
                        chatArea.appendChild(greeting);
                    } else {
                        const div = document.createElement('div');
                        div.className = 'message assistant';
                        div.innerHTML = 'Hello! Select an indexed project workspace and ask me questions about your Java/Spring Boot code. Click <b>⚡ Index Folder</b> to scan your current directory.';
                        chatArea.appendChild(div);
                    }

                    const history = message.history || [];
                    history.forEach(m => {
                        if (m.role === 'user') {
                            renderMessage(m.content, 'user');
                        } else {
                            const div = document.createElement('div');
                            div.className = 'message assistant';
                            div.innerHTML = '<span class="content">' + formatTextToHtml(m.content) + '</span>';
                            chatArea.appendChild(div);
                        }
                    });
                    scrollToBottom();
                    break;
                }
            }
        });

        function updateProjectSelect(workspaces, activeId) {
            select.innerHTML = '';
            if (workspaces.length === 0) {
                const opt = document.createElement('option');
                opt.value = '';
                opt.textContent = '-- No projects indexed --';
                select.appendChild(opt);
                updateStatusBadge();
                return;
            }

            workspaces.forEach(w => {
                const opt = document.createElement('option');
                opt.value = w.project_id;
                opt.textContent = w.alias + (w.is_active ? ' (active)' : '');
                if (w.project_id === activeId || w.is_active) {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });
            updateStatusBadge();

            // Trigger history restore for the active project
            if (select.value) {
                vscode.postMessage({
                    type: 'selectProject',
                    projectId: select.value
                });
            }
        }

        function renderMessage(text, sender) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            div.textContent = text;
            chatArea.appendChild(div);
            scrollToBottom();
        }

        function renderAssistantPlaceholder(id) {
            const div = document.createElement('div');
            div.className = 'message assistant';
            div.id = id;
            div.innerHTML = '<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div><span class="content"></span>';
            chatArea.appendChild(div);
            scrollToBottom();
        }

        function renderAssistantMetadata(bubble, response) {
            if (response.citations && response.citations.length > 0) {
                const citeContainer = document.createElement('div');
                citeContainer.className = 'citations-container';
                citeContainer.innerHTML = '<div class="citations-title">CITATIONS & REFERENCES:</div>';

                response.citations.forEach((c, idx) => {
                    const btn = document.createElement('div');
                    btn.className = 'citation-badge';
                    const fileBase = c.file_path.split('/').pop().split('\\\\').pop();
                    btn.textContent = '[' + (idx + 1) + '] ' + fileBase + (c.start_line ? ':' + c.start_line : '');
                    btn.title = c.file_path + (c.start_line ? ' (Lines ' + c.start_line + '-' + c.end_line + ')' : '');
                    
                    btn.addEventListener('click', () => {
                        vscode.postMessage({
                            type: 'openFile',
                            filePath: c.file_path,
                            startLine: c.start_line,
                            endLine: c.end_line
                        });
                    });

                    citeContainer.appendChild(btn);
                });

                bubble.appendChild(citeContainer);
            }

            const footer = document.createElement('div');
            footer.className = 'metadata-footer';
            footer.innerHTML = '<span>Model: ' + response.modelName + '</span><span>Duration: ' + (response.durationMs / 1000).toFixed(2) + 's</span>';
            bubble.appendChild(footer);
            
            scrollToBottom();
        }

        window.copyCodeBlock = function(btn) {
            const pre = btn.closest('.code-block-container').querySelector('pre');
            const codeText = pre.innerText || pre.textContent;
            navigator.clipboard.writeText(codeText).then(() => {
                const originalInner = btn.innerHTML;
                btn.innerHTML = 
                    '<svg viewBox="0 0 24 24" width="12" height="12" stroke="#10b981" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">' +
                        '<polyline points="20 6 9 17 4 12"></polyline>' +
                    '</svg>' +
                    'Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalInner;
                }, 2000);
            });
        };

        function formatTextToHtml(text) {
            let escaped = text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");

            const codeBlocks = [];
            const triple = String.fromCharCode(96) + String.fromCharCode(96) + String.fromCharCode(96);
            const blockRegex = new RegExp(triple + "([a-zA-Z0-9_+-]*)\\\\n([\\\\s\\\\S]*?)(?:\\\\n)?" + triple, "g");
            escaped = escaped.replace(blockRegex, function(match, lang, code) {
                const placeholder = '___CODEBLOCK_' + codeBlocks.length + '___';
                const language = lang.trim() || 'code';
                const codeHtml = 
                    '<div class="code-block-container">' +
                        '<div class="code-block-header">' +
                            '<span class="code-block-lang"><span class="code-icon">&lt;/&gt;</span> ' + language + '</span>' +
                            '<button class="btn-copy" onclick="copyCodeBlock(this)">' +
                                '<svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">' +
                                    '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>' +
                                    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>' +
                                '</svg>' +
                                'Copy' +
                            '</button>' +
                        '</div>' +
                        '<pre><code>' + code + '</code></pre>' +
                    '</div>';
                codeBlocks.push(codeHtml);
                return placeholder;
            });

            const single = String.fromCharCode(96);
            const inlineRegex = new RegExp(single + "([^" + single + "]+)" + single, "g");
            escaped = escaped.replace(inlineRegex, '<code>$1</code>');

            escaped = escaped.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
            escaped = escaped.replace(/\\*(.*?)\\*/g, '<em>$1</em>');

            const lines = escaped.split('\\n');
            let html = [];
            let listStack = [];

            function closeLists(toLevel) {
                while (listStack.length > toLevel) {
                    listStack.pop();
                    html.push('</ul>');
                }
            }

            for (let i = 0; i < lines.length; i++) {
                let line = lines[i];
                let trimmed = line.trim();

                if (trimmed.startsWith('### ')) {
                    closeLists(0);
                    html.push('<h3>' + trimmed.substring(4) + '</h3>');
                    continue;
                } else if (trimmed.startsWith('## ')) {
                    closeLists(0);
                    html.push('<h2>' + trimmed.substring(3) + '</h2>');
                    continue;
                } else if (trimmed.startsWith('# ')) {
                    closeLists(0);
                    html.push('<h1>' + trimmed.substring(2) + '</h1>');
                    continue;
                }

                let listMatch = line.match(/^(\\s*)[\\-\\*]\\s+(.*?)$/);
                if (listMatch) {
                    let indent = listMatch[1].length;
                    let content = listMatch[2];

                    let level = listStack.indexOf(indent);
                    if (level === -1) {
                        listStack.push(indent);
                        html.push('<ul>');
                        level = listStack.length - 1;
                    } else {
                        closeLists(level + 1);
                    }

                    html.push('<li>' + content + '</li>');
                } else {
                    if (trimmed === '') {
                        closeLists(0);
                        html.push('<br>');
                    } else {
                        closeLists(0);
                        html.push('<div class="text-line">' + line + '</div>');
                    }
                }
            }
            closeLists(0);

            let finalHtml = html.join('');
            
            for (let idx = 0; idx < codeBlocks.length; idx++) {
                const placeholder = '___CODEBLOCK_' + idx + '___';
                finalHtml = finalHtml.replace('<div class="text-line">' + placeholder + '</div>', codeBlocks[idx]);
                finalHtml = finalHtml.replace(placeholder, codeBlocks[idx]);
            }

            finalHtml = finalHtml.replace(/<br><\\/h[1-3]>/g, '</h$1>');
            finalHtml = finalHtml.replace(/<br><\\/ul>/g, '</ul>');
            finalHtml = finalHtml.replace(/<br><\\/li>/g, '</li>');
            finalHtml = finalHtml.replace(/<br><ul>/g, '<ul>');

            return finalHtml;
        }

        function updateModelDropdown(models, selected) {
            if (!modelSelect || !selectedModelLabel) return;
            modelSelect.innerHTML = '';
            
            if (models.length === 0) {
                const opt = document.createElement('option');
                opt.value = selected || 'qwen2.5-coder:3b';
                opt.textContent = selected || 'qwen2.5-coder:3b';
                modelSelect.appendChild(opt);
                selectedModelLabel.textContent = selected || 'qwen2.5-coder:3b';
                return;
            }

            models.forEach(model => {
                const opt = document.createElement('option');
                opt.value = model;
                opt.textContent = model;
                if (model === selected) {
                    opt.selected = true;
                }
                modelSelect.appendChild(opt);
            });

            selectedModelLabel.textContent = selected || models[0];
        }

        if (modelSelect) {
            modelSelect.addEventListener('change', () => {
                const val = modelSelect.value;
                selectedModelLabel.textContent = val;
                vscode.postMessage({
                    type: 'modelChanged',
                    model: val
                });
            });
        }

        function escapeHtml(text) {
            if (!text) return "";
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
        }

        function scrollToBottom() {
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    </script>
</body>
</html>`;
    }
}
