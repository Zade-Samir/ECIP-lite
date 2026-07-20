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
    <title>Agent Chat</title>
    <style>
        :root {
            --bg-color: #181818;
            --input-container-bg: #222222;
            --border-color: rgba(255, 255, 255, 0.06);
            --text-primary: #e3e3e3;
            --text-secondary: #cbd5e1;
            --text-muted: #8e8e8e;
            --code-header-bg: #1e1e1e;
            --code-body-bg: #111111;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 16px;
            display: flex;
            flex-direction: column;
            height: 100vh;
            box-sizing: border-box;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 2px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .header-title {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
        }

        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .header-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 14px;
            padding: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.15s;
        }

        .header-btn:hover {
            color: var(--text-primary);
        }

        .active-project-container {
            margin-bottom: 6px;
        }

        .active-project-label {
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            user-select: none;
        }

        .active-project-label:hover {
            opacity: 0.85;
        }

        select#project-select {
            display: none;
            background: #222222;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            outline: none;
            margin-top: 4px;
            width: 100%;
            cursor: pointer;
        }

        .chat-area {
            flex-grow: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
            margin-bottom: 12px;
            padding-right: 4px;
        }

        .message {
            font-size: 13px;
            line-height: 1.6;
            word-wrap: break-word;
            animation: fadeIn 0.15s ease-out forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            color: #ffffff;
            font-weight: 500;
            align-self: flex-start;
            border-left: 2px solid #3b82f6;
            padding-left: 10px;
            margin-left: 2px;
        }

        .message.assistant {
            color: var(--text-primary);
            align-self: flex-start;
            width: 100%;
        }

        .message.error {
            background: rgba(239, 68, 68, 0.08);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 8px 12px;
            border-radius: 8px;
            align-self: center;
            width: 100%;
            box-sizing: border-box;
        }

        /* Clean Code block wrapper */
        .code-wrapper {
            margin: 12px 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            background: var(--code-body-bg);
        }

        .code-header {
            background: var(--code-header-bg);
            padding: 6px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 500;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }

        .copy-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 10px;
            transition: all 0.15s;
        }

        .copy-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.1);
        }

        .message pre {
            margin: 0;
            padding: 12px;
            overflow-x: auto;
        }

        .message code {
            font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            color: #60a5fa;
            background: rgba(255, 255, 255, 0.03);
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
            margin-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
            padding-top: 10px;
        }

        .citations-title {
            font-size: 10px;
            color: var(--text-muted);
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .citation-badge {
            display: inline-flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
            margin-right: 6px;
            margin-bottom: 6px;
            transition: all 0.15s ease;
        }

        .citation-badge:hover {
            background: rgba(255, 255, 255, 0.08);
            color: white;
            border-color: rgba(255, 255, 255, 0.15);
        }

        .metadata-footer {
            font-size: 9px;
            color: var(--text-muted);
            margin-top: 10px;
            display: flex;
            justify-content: space-between;
            border-top: 1px solid rgba(255, 255, 255, 0.02);
            padding-top: 6px;
        }

        /* Unified Input Container */
        .input-container {
            background-color: var(--input-container-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            margin-bottom: 8px;
            transition: border-color 0.2s;
        }

        .input-container:focus-within {
            border-color: rgba(255, 255, 255, 0.12);
        }

        textarea {
            width: 100%;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            padding: 12px 14px 4px 14px;
            font-size: 13px;
            resize: none;
            height: 48px;
            font-family: inherit;
            box-sizing: border-box;
        }

        textarea::placeholder {
            color: #6b7280;
        }

        .input-bottom-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 10px 10px 10px;
        }

        .input-bottom-left {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .input-bottom-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .input-action-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 14px;
            cursor: pointer;
            padding: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.15s;
        }

        .input-action-btn:hover {
            color: var(--text-primary);
        }

        .model-badge {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            user-select: none;
        }

        .model-badge:hover {
            color: var(--text-primary);
            border-color: rgba(255, 255, 255, 0.12);
        }

        .disclaimer {
            font-size: 10px;
            color: #555555;
            text-align: center;
            margin-top: 4px;
            margin-bottom: 4px;
            user-select: none;
        }

        .loading-dots {
            display: inline-flex;
            gap: 4px;
            align-items: center;
            height: 12px;
            margin-right: 6px;
        }

        .dot {
            width: 5px;
            height: 5px;
            background-color: var(--text-muted);
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
        <div class="header-title">Agent</div>
        <div class="header-actions">
            <button class="header-btn" id="btn-refresh" title="Refresh Workspaces">🔄</button>
            <button class="header-btn" id="btn-index-curr" title="Index Current Folder">⚡</button>
        </div>
    </div>

    <div class="active-project-container">
        <div class="active-project-label" id="project-label" onclick="toggleProjectDropdown()">
            <span id="active-project-name">Loading...</span> <span style="font-size: 8px; opacity: 0.5;">▼</span>
        </div>
        <select id="project-select" onchange="selectProject(this.value)">
            <option value="">Loading workspaces...</option>
        </select>
    </div>

    <div class="chat-area" id="chat-area">
        <div class="message assistant">
            Hello! Select an indexed project workspace and ask me questions about your Java/Spring Boot code. Click the <b>⚡</b> header icon to register and index your current directory.
        </div>
    </div>

    <div class="input-container">
        <textarea id="question-input" placeholder="Ask anything, @ to mention, / for actions"></textarea>
        <div class="input-bottom-bar">
            <div class="input-bottom-left">
                <button class="input-action-btn" title="Add files">+</button>
                <div class="model-badge">
                    <span id="active-model-name">Gemini 3.5 Flash (Medium)</span> <span style="font-size: 8px; opacity: 0.5;">▼</span>
                </div>
            </div>
            <div class="input-bottom-right">
                <button class="input-action-btn" style="margin-right: 4px;" title="Voice input">🎙️</button>
                <button class="input-action-btn" id="btn-send" title="Send question">➡️</button>
            </div>
        </div>
    </div>

    <div class="disclaimer">
        AI may make mistakes. Double-check all generated code.
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const select = document.getElementById('project-select');
        const refreshBtn = document.getElementById('btn-refresh');
        const indexCurrBtn = document.getElementById('btn-index-curr');
        const sendBtn = document.getElementById('btn-send');
        const input = document.getElementById('question-input');
        const chatArea = document.getElementById('chat-area');

        // Toggle dropdown display
        window.toggleProjectDropdown = function() {
            select.style.display = 'block';
            select.focus();

            const hide = () => {
                select.style.display = 'none';
            };
            select.addEventListener('change', hide, { once: true });
            select.addEventListener('blur', hide, { once: true });
        };

        window.selectProject = function(val) {
            select.value = val;
            const selectedText = select.options[select.selectedIndex]?.text || '';
            document.getElementById('active-project-name').textContent = selectedText.replace(' (active)', '');
        };

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
                document.getElementById('active-project-name').textContent = 'No Workspace';
                return;
            }

            let activeName = '';
            workspaces.forEach(w => {
                const opt = document.createElement('option');
                opt.value = w.project_id;
                opt.textContent = w.alias;
                if (w.project_id === activeId || w.is_active) {
                    opt.selected = true;
                    activeName = w.alias;
                }
                select.appendChild(opt);
            });

            if (!activeName && workspaces.length > 0) {
                select.options[0].selected = true;
                activeName = workspaces[0].alias;
            }
            document.getElementById('active-project-name').textContent = activeName;
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
                    const fileBase = c.file_path.split('/').pop().split('\\').pop();
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
                .replace(/&lt;/g, "&lt;")
                .replace(/&gt;/g, "&gt;");

            // Format code blocks without using raw backticks
            const triple = String.fromCharCode(96) + String.fromCharCode(96) + String.fromCharCode(96);
            const blockRegex = new RegExp(triple + "(\\w*)\\n([\\s\\S]*?)\\n" + triple, "g");
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
            escaped = escaped.replace(/\n/g, '<br>');

            return escaped;
        }

        // Auto scroll to bottom
        function scrollToBottom() {
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    </script>
</body>
</html>`;
    }
}
