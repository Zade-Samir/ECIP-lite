package com.samirzade.ecip.api

import com.intellij.openapi.components.service
import com.samirzade.ecip.settings.EcipSettings
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration

class EcipClient {
    private val httpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(10))
        .build()

    private val settings = service<EcipSettings>()

    fun getApiUrl(): String {
        return settings.apiUrl.trimEnd('/')
    }

    fun listWorkspaces(): String {
        val request = HttpRequest.newBuilder()
            .uri(URI.create("${getApiUrl()}/api/v1/workspaces"))
            .GET()
            .build()
        val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
        return response.body()
    }

    fun registerWorkspace(projectId: String, path: String): String {
        val json = """{"project_id": "$projectId", "alias": "$projectId", "root_path": "$path"}"""
        val request = HttpRequest.newBuilder()
            .uri(URI.create("${getApiUrl()}/api/v1/workspaces"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build()
        val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
        return response.body()
    }

    fun indexProject(path: String, alias: String): String {
        val json = """{"project_path": "$path", "project_alias": "$alias"}"""
        val request = HttpRequest.newBuilder()
            .uri(URI.create("${getApiUrl()}/api/v1/index"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build()
        val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
        return response.body()
    }

    fun query(projectId: String, question: String): String {
        val escapedQuestion = question.replace("\"", "\\\"").replace("\n", "\\n")
        val json = """{"project_id": "$projectId", "question": "$escapedQuestion", "stream": false}"""
        val request = HttpRequest.newBuilder()
            .uri(URI.create("${getApiUrl()}/api/v1/query"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build()
        val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
        return response.body()
    }
}
