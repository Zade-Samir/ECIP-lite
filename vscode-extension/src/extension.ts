import * as vscode from 'vscode';
import { SidebarProvider } from './sidebarProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('ECIP Lite Extension is now active!');

    // Initialize the sidebar view provider
    const sidebarProvider = new SidebarProvider(context.extensionUri);

    // Register with VS Code
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            SidebarProvider.viewType,
            sidebarProvider
        )
    );
}

export function deactivate() {}
