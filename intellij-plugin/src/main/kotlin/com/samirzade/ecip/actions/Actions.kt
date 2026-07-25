package com.samirzade.ecip.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.ui.Messages
import com.intellij.openapi.wm.ToolWindowManager
import com.samirzade.ecip.api.EcipClient
import javax.swing.JTextArea

abstract class BaseEcipAction : AnAction() {
    protected val client = EcipClient()

    protected fun sendToToolWindow(project: com.intellij.openapi.project.Project, prompt: String) {
        val toolWindow = ToolWindowManager.getInstance(project).getToolWindow("ECIP Chat")
        if (toolWindow != null) {
            toolWindow.show {
                val content = toolWindow.contentManager.getContent(0)
                val panel = content?.component as? javax.swing.JPanel
                val scrollPane = panel?.getComponent(0) as? javax.swing.JScrollPane
                val viewport = scrollPane?.viewport
                val chatArea = viewport?.view as? JTextArea
                
                if (chatArea != null) {
                    chatArea.append("You (context): $prompt\n\n")
                    Thread {
                        try {
                            val response = client.query(project.name, prompt)
                            javax.swing.SwingUtilities.invokeLater {
                                chatArea.append("ECIP: $response\n\n")
                            }
                        } catch (e: Exception) {
                            javax.swing.SwingUtilities.invokeLater {
                                chatArea.append("Error: ${e.message}\n\n")
                            }
                        }
                    }.start()
                }
            }
        }
    }
}

class AskQuestionAction : BaseEcipAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val question = Messages.showInputDialog(
            project,
            "Ask ECIP a question about the codebase:",
            "Ask ECIP",
            Messages.getQuestionIcon()
        )
        if (!question.isNullOrEmpty()) {
            sendToToolWindow(project, question)
        }
    }
}

class ExplainSelectionAction : BaseEcipAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        val selectionModel = editor.selectionModel
        val selectedText = selectionModel.selectedText
        
        if (!selectedText.isNullOrEmpty()) {
            sendToToolWindow(project, "Explain this code selection:\n```java\n$selectedText\n```")
        } else {
            Messages.showWarningDialog(project, "Please select some code to explain first.", "No Selection")
        }
    }
}

class ExplainClassAction : BaseEcipAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val psiFile = e.getData(CommonDataKeys.PSI_FILE) ?: return
        val className = psiFile.name.substringBeforeLast(".")
        sendToToolWindow(project, "Explain the purpose and structure of the class: $className")
    }
}

class ShowDependenciesAction : BaseEcipAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val psiFile = e.getData(CommonDataKeys.PSI_FILE) ?: return
        val className = psiFile.name.substringBeforeLast(".")
        sendToToolWindow(project, "Show dependencies and class relationships for class $className")
    }
}

class IndexProjectAction : BaseEcipAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val projectPath = project.basePath
        
        if (projectPath != null) {
            Thread {
                try {
                    client.registerWorkspace(project.name, projectPath)
                    client.indexProject(projectPath, project.name)
                    javax.swing.SwingUtilities.invokeLater {
                        Messages.showInfoMessage(project, "Project successfully indexed in ECIP!", "Indexing Complete")
                    }
                } catch (ex: Exception) {
                    javax.swing.SwingUtilities.invokeLater {
                        Messages.showErrorDialog(project, "Indexing failed: ${ex.message}", "Error")
                    }
                }
            }.start()
        }
    }
}

class OpenCitationsAction : BaseEcipAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        sendToToolWindow(project, "Show recent source code citations for my queries")
    }
}
