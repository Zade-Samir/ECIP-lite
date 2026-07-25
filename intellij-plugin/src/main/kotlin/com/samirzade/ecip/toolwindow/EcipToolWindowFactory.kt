package com.samirzade.ecip.toolwindow

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import com.samirzade.ecip.api.EcipClient
import java.awt.BorderLayout
import java.awt.Dimension
import javax.swing.*

class EcipToolWindowFactory : ToolWindowFactory {
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val panel = JPanel(BorderLayout())
        
        val chatArea = JTextArea()
        chatArea.isEditable = false
        chatArea.lineWrap = true
        chatArea.wrapStyleWord = true
        
        val scrollPane = JScrollPane(chatArea)
        panel.add(scrollPane, BorderLayout.CENTER)
        
        val inputPanel = JPanel(BorderLayout())
        val inputField = JTextField()
        val sendButton = JButton("Send")
        
        val client = EcipClient()
        
        fun sendQuery() {
            val text = inputField.text.trim()
            if (text.isEmpty()) return
            
            chatArea.append("You: $text\n\n")
            inputField.text = ""
            
            // Execute in background
            Thread {
                try {
                    val response = client.query(project.name, text)
                    SwingUtilities.invokeLater {
                        chatArea.append("ECIP: $response\n\n")
                    }
                } catch (e: Exception) {
                    SwingUtilities.invokeLater {
                        chatArea.append("Error: ${e.message}\n\n")
                    }
                }
            }.start()
        }
        
        sendButton.addActionListener { sendQuery() }
        inputField.addActionListener { sendQuery() }
        
        inputPanel.add(inputField, BorderLayout.CENTER)
        inputPanel.add(sendButton, BorderLayout.EAST)
        inputPanel.setPreferredSize(Dimension(0, 50))
        
        panel.add(inputPanel, BorderLayout.SOUTH)
        
        val content = ContentFactory.getInstance().createContent(panel, "", false)
        toolWindow.contentManager.addContent(content)
    }
}
