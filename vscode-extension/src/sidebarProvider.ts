import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'ecip-lite-chat-view';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

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

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from the Webview UI
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'getWorkspaces': {
                    await this.fetchWorkspaces();
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
            }
        });

        // Fetch workspaces on load
        this.fetchWorkspaces();
    }

    private async fetchWorkspaces() {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/workspaces');
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
                const regResponse = await fetch('http://127.0.0.1:8000/api/v1/workspaces', {
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
                const indexResponse = await fetch('http://127.0.0.1:8000/api/v1/index', {
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

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    question: question
                })
            });

            if (!response.ok) {
                const errorData: any = await response.json();
                throw new Error(errorData.detail || `Server responded with ${response.status}`);
            }

            const data: any = await response.json();
            this._view?.webview.postMessage({
                type: 'queryResponse',
                answer: data.answer,
                citations: data.citations || [],
                modelName: data.model_name || 'local-llm',
                durationMs: data.duration_ms || 0
            });
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
            --bg-gradient: linear-gradient(135deg, #090d16 0%, #111827 100%);
            --card-bg: rgba(30, 41, 59, 0.55);
            --card-border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(59, 130, 246, 0.4);
            --accent-color: #3b82f6;
            --accent-gradient: linear-gradient(90deg, #60a5fa, #3b82f6);
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --glow-shadow: 0 0 15px rgba(59, 130, 246, 0.15);
            --code-header-bg: #1e293b;
            --code-body-bg: #090d16;
        }

        body {
            background: var(--bg-gradient);
            color: var(--text-primary);
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 14px;
            display: flex;
            flex-direction: column;
            height: 100vh;
            box-sizing: border-box;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 10px;
        }

        .header h3 {
            margin: 0;
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #38bdf8, #3b82f6, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
        }

        .project-selector {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: var(--glow-shadow);
        }

        .project-selector label {
            font-size: 10px;
            color: var(--text-muted);
            font-weight: 600;
            letter-spacing: 0.8px;
        }

        .select-row {
            display: flex;
            gap: 8px;
        }

        select {
            flex-grow: 1;
            background: #090d16;
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            outline: none;
            cursor: pointer;
            transition: border-color 0.2s;
        }

        select:focus {
            border-color: var(--accent-color);
        }

        button.btn-icon {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }

        button.btn-icon:hover {
            color: var(--text-primary);
            border-color: var(--accent-color);
            background: rgba(59, 130, 246, 0.1);
        }

        button.btn-primary {
            background: var(--accent-gradient);
            border: none;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }

        button.btn-primary:hover {
            opacity: 0.95;
        }

        button.btn-primary:active {
            transform: scale(0.98);
        }

        .chat-area {
            flex-grow: 1;
            overflow-y: auto;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            background: rgba(17, 24, 39, 0.3);
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            margin-bottom: 14px;
        }

        .message {
            max-width: 90%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.6;
            word-wrap: break-word;
            animation: slideIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 3px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }

        .message.assistant {
            background: var(--card-bg);
            color: var(--text-primary);
            align-self: flex-start;
            border-bottom-left-radius: 3px;
            border: 1px solid var(--card-border);
        }

        .message.error {
            background: rgba(239, 68, 68, 0.08);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.25);
            align-self: center;
            max-width: 100%;
        }

        /* Structured Code Block styling */
        .code-wrapper {
            margin: 10px 0;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid var(--card-border);
            background: var(--code-body-bg);
        }

        .code-header {
            background: var(--code-header-bg);
            padding: 4px 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 500;
            border-bottom: 1px solid var(--card-border);
        }

        .copy-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-secondary);
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 10px;
            transition: all 0.1s;
        }

        .copy-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.12);
        }

        .message pre {
            margin: 0;
            padding: 10px;
            overflow-x: auto;
        }

        .message code {
            font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            color: #60a5fa;
            background: rgba(0, 0, 0, 0.2);
            padding: 2px 4px;
            border-radius: 4px;
        }

        .message pre code {
            color: #e2e8f0;
            background: none;
            padding: 0;
            border-radius: 0;
            white-space: pre;
        }

        .citations-container {
            margin-top: 12px;
            border-top: 1px dashed var(--card-border);
            padding-top: 8px;
        }

        .citations-title {
            font-size: 10px;
            color: var(--text-muted);
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            text-transform: uppercase;
        }

        .citation-badge {
            display: inline-flex;
            align-items: center;
            background: rgba(59, 130, 246, 0.08);
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
            margin-right: 6px;
            margin-bottom: 6px;
            transition: all 0.15s ease;
        }

        .citation-badge:hover {
            background: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
            box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
        }

        .metadata-footer {
            font-size: 9px;
            color: var(--text-muted);
            margin-top: 8px;
            display: flex;
            justify-content: space-between;
            border-top: 1px solid rgba(255, 255, 255, 0.03);
            padding-top: 6px;
        }

        .input-row {
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }

        textarea {
            flex-grow: 1;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 10px;
            border-radius: 8px;
            font-size: 13px;
            outline: none;
            resize: none;
            height: 38px;
            font-family: inherit;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        textarea:focus {
            border-color: var(--accent-color);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
        }

        button.btn-send {
            background: var(--accent-gradient);
            border: none;
            color: white;
            width: 38px;
            height: 38px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s, opacity 0.2s;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);
        }

        button.btn-send:hover {
            opacity: 0.95;
        }

        button.btn-send:active {
            transform: scale(0.95);
        }

        .loading-dots {
            display: inline-flex;
            gap: 4px;
            align-items: center;
            height: 12px;
            margin-right: 6px;
        }

        .dot {
            width: 6px;
            height: 6px;
            background-color: var(--accent-color);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h3>ECIP LITE CORE</h3>
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
    </div>

    <div class="chat-area" id="chat-area">
        <div class="message assistant">
            Hello! Select an indexed project workspace and ask me questions about your Java/Spring Boot code. Click <b>⚡ Index Folder</b> to scan your current directory.
        </div>
    </div>

    <div class="input-row">
        <textarea id="question-input" placeholder="Ask a question about the code..."></textarea>
        <button class="btn-send" id="btn-send" title="Send question">➡️</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const select = document.getElementById('project-select');
        const refreshBtn = document.getElementById('btn-refresh');
        const indexCurrBtn = document.getElementById('btn-index-curr');
        const sendBtn = document.getElementById('btn-send');
        const input = document.getElementById('question-input');
        const chatArea = document.getElementById('chat-area');

        // Copy functionality for code blocks
        window.copyCode = function(button) {
            var pre = button.parentElement.nextElementSibling;
            var code = pre.querySelector('code').innerText;
            navigator.clipboard.writeText(code).then(function() {
                var originalText = button.textContent;
                button.textContent = 'Copied!';
                button.style.color = '#34d399';
                setTimeout(function() {
                    button.textContent = originalText;
                    button.style.color = '';
                }, 2000);
            });
        };

        // Refresh action
        refreshBtn.addEventListener('click', () => {
            vscode.postMessage({ type: 'getWorkspaces' });
        });

        // Index current folder
        indexCurrBtn.addEventListener('click', () => {
            vscode.postMessage({ type: 'indexCurrentWorkspace' });
        });

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

            // Render assistant loading state
            const loadingId = 'loading-' + Date.now();
            renderLoadingMessage(loadingId);

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

        // Handle message signals from Extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'workspacesList': {
                    updateProjectSelect(message.workspaces, message.active);
                    break;
                }
                case 'backendError': {
                    renderMessage(message.message, 'error');
                    break;
                }
                case 'queryResponse': {
                    // Remove loading placeholder
                    removeLoadingPlaceholder();

                    if (message.error) {
                        renderMessage(message.error, 'error');
                    } else {
                        renderAssistantResponse(message);
                    }
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
        }

        function renderMessage(text, sender) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            div.textContent = text;
            chatArea.appendChild(div);
            scrollToBottom();
        }

        function renderLoadingMessage(id) {
            const div = document.createElement('div');
            div.className = 'message assistant';
            div.id = id;
            div.innerHTML = '<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div> Analyzing codebase...';
            chatArea.appendChild(div);
            scrollToBottom();
        }

        function removeLoadingPlaceholder() {
            const loaders = chatArea.querySelectorAll('[id^="loading-"]');
            loaders.forEach(l => l.remove());
        }

        function renderAssistantResponse(response) {
            const div = document.createElement('div');
            div.className = 'message assistant';

            // Simple markdown-style parser for formatting responses
            let rawAnswer = response.answer;
            let htmlContent = formatTextToHtml(rawAnswer);

            div.innerHTML = htmlContent;

            // Add citations if available
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

                div.appendChild(citeContainer);
            }

            // Performance metrics footer
            const footer = document.createElement('div');
            footer.className = 'metadata-footer';
            footer.innerHTML = '<span>Model: ' + response.modelName + '</span><span>Duration: ' + (response.durationMs / 1000).toFixed(2) + 's</span>';
            div.appendChild(footer);

            chatArea.appendChild(div);
            scrollToBottom();
        }

        function formatTextToHtml(text) {
            // Escape tags to prevent raw HTML injections
            let escaped = text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");

            // Format code blocks without using raw backticks
            const triple = String.fromCharCode(96) + String.fromCharCode(96) + String.fromCharCode(96);
            const blockRegex = new RegExp(triple + "(\\\\w*)\\\\n([\\\\s\\\\S]*?)\\\\n" + triple, "g");
            escaped = escaped.replace(blockRegex, function(match, lang, code) {
                return '<div class="code-wrapper">' +
                       '<div class="code-header"><span>' + (lang || 'Java') + '</span><button class="copy-btn" onclick="copyCode(this)">Copy</button></div>' +
                       '<pre><code>' + code + '</code></pre>' +
                       '</div>';
            });

            // Format inline code without using raw backticks
            const single = String.fromCharCode(96);
            const inlineRegex = new RegExp(single + "([^" + single + "]+)" + single, "g");
            escaped = escaped.replace(inlineRegex, '<code>$1</code>');

            // Format line breaks
            escaped = escaped.replace(/\\n/g, '<br>');

            return escaped;
        }

        function scrollToBottom() {
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    </script>
</body>
</html>`;
    }
}
