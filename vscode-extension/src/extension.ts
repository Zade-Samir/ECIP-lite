import * as vscode from 'vscode';
import * as path from 'path';
import { SidebarProvider, ProposedContentProvider } from './sidebarProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('ECIP Lite Extension is now active!');

    // Register proposed content provider for side-by-side diff review
    context.subscriptions.push(
        vscode.workspace.registerTextDocumentContentProvider(
            'ecip-proposed',
            ProposedContentProvider.getInstance()
        )
    );

    // Initialize the sidebar view provider
    const sidebarProvider = new SidebarProvider(context);

    // Register with VS Code
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            SidebarProvider.viewType,
            sidebarProvider
        )
    );

    // 1. ECIP: Ask Question
    context.subscriptions.push(
        vscode.commands.registerCommand('ecip-lite.askQuestion', async () => {
            const question = await vscode.window.showInputBox({
                prompt: 'Ask ECIP a question about the codebase',
                placeHolder: 'e.g. What does UserService do?'
            });
            if (question) {
                sidebarProvider.askQuestion(question);
            }
        })
    );

    // 2. ECIP: Explain Selection
    context.subscriptions.push(
        vscode.commands.registerCommand('ecip-lite.explainSelection', () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                const selection = editor.document.getText(editor.selection);
                if (selection) {
                    sidebarProvider.askQuestion(`Explain this code selection:\n\`\`\`java\n${selection}\n\`\`\``);
                } else {
                    vscode.window.showWarningMessage('Please select some code to explain first.');
                }
            } else {
                vscode.window.showWarningMessage('Open a code file to explain selection.');
            }
        })
    );

    // 3. ECIP: Index Workspace
    context.subscriptions.push(
        vscode.commands.registerCommand('ecip-lite.indexWorkspace', () => {
            sidebarProvider.indexCurrentWorkspace();
        })
    );

    // 4. ECIP: Show Dependencies
    context.subscriptions.push(
        vscode.commands.registerCommand('ecip-lite.showDependencies', () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                const doc = editor.document;
                const fileName = path.basename(doc.fileName, '.java');
                sidebarProvider.askQuestion(`Show dependencies and class relationships for class ${fileName}`);
            } else {
                vscode.window.showWarningMessage('Open a class file to show dependencies.');
            }
        })
    );

    // 5. ECIP: Open Citations
    context.subscriptions.push(
        vscode.commands.registerCommand('ecip-lite.openCitations', () => {
            sidebarProvider.askQuestion('Show recent source code citations for my queries');
        })
    );

    // 6. Auto re-index on file save (debounced, only supported file types)
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            sidebarProvider.indexSingleFile(document.uri.fsPath);
        })
    );
}

export function deactivate() {}
