# 🧪 ECIP Extension & AI Copilots Testing Guide

This guide provides **ready-to-use, copy-pasteable prompts** so you can test and observe every single ECIP Feature & AI Copilot described in the `README.md` directly inside your **VS Code Extension** or Chat UI!

---

## 🎯 How to Test Using Your Extension

1. Ensure your local API server is running (`python run_api.py`).
2. Make sure you have clicked **⚡ Index Folder** or indexed a sample project (e.g., in `projects/`).
3. Open your **ECIP VS Code Extension** side panel.
4. Copy any prompt from the sections below, paste it into the Extension chat, and observe the live streaming answer and citations!

---

## 1. 👥 AI Pair Programmer & Codebase Q&A
*Tests: Workspace context assembly, multi-turn dialogue, and `file:line` source citations.*

### 📋 Test Prompts:
```text
Explain what the main components and services of this indexed codebase are.
```
```text
What REST endpoints are exposed in this project, and which controllers handle them?
```
```text
Which classes or methods depend on the UserRepository or database layer?
```

---

## 2. 🐞 AI Debugging Assistant & Root Cause Analysis
*Tests: Stack trace analysis, log correlation, and confidence-scored fix recommendations.*

### 📋 Test Prompts:
```text
Analyze this stack trace and tell me the root cause and how to fix it:

java.lang.NullPointerException: Cannot invoke "String.length()" because "userToken" is null
    at com.example.service.UserService.validateToken(UserService.java:45)
    at com.example.controller.UserController.login(UserController.java:22)
```
```text
I am seeing high memory usage and a OutOfMemoryError in a loop. How can I debug and prevent memory leaks in Java Spring Boot services?
```

---

## 3. 🔍 AI Code Review Assistant
*Tests: Code diff analysis, severity classification (HIGH/MEDIUM/LOW), and inline suggestions.*

### 📋 Test Prompts:
```text
Please perform a code review on this pull request diff snippet and list any security or quality issues:

+++ b/src/main/java/com/example/controller/UserController.java
+ String query = "SELECT * FROM users WHERE name = '" + username + "'";
+ Statement stmt = connection.createStatement();
+ ResultSet rs = stmt.executeQuery(query);
+ System.out.println("User query executed: " + query);
```

---

## 4. 🧪 AI Test Generation Assistant
*Tests: Automated JUnit 5 / Pytest generation, mock creation, and coverage impact estimation.*

### 📋 Test Prompts:
```text
Generate a complete JUnit 5 unit test class with Mockito mocks for the UserController class. Include positive and negative test cases.
```
```text
Generate unit tests for a method that validates user email addresses and throws an InvalidEmailException on invalid inputs.
```

---

## 5. 📄 AI Documentation Assistant
*Tests: API Reference generation, Markdown export, and stale documentation detection.*

### 📋 Test Prompts:
```text
Generate a clean Markdown API Reference document for all REST endpoints in the project, including HTTP methods, paths, and descriptions.
```
```text
Write a concise README onboarding guide for a new developer joining this repository.
```

---

## 6. 🏗️ AI Architecture Copilot & ADR Generator
*Tests: Design pattern suggestions, layer violation checks, and Architectural Decision Record (ADR) creation.*

### 📋 Test Prompts:
```text
Draft an Architectural Decision Record (ADR) proposing to switch from synchronous REST HTTP calls to an Event-Driven Architecture with Kafka.
```
```text
Analyze layer architecture: Is it bad practice for a REST Controller to access a Database Repository directly without a Service layer? Explain the trade-offs.
```

---

## 7. 🚀 AI DevOps Copilot
*Tests: Kubernetes manifest validation, Dockerfile optimization, and resource limit checks.*

### 📋 Test Prompts:
```text
Review this Kubernetes Deployment manifest for resource limits, security context, and best practices:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: user-app
        image: user-service:latest
        ports:
        - containerPort: 8080
```

---

## 8. 🛡️ Security Intelligence & Secret Scanner
*Tests: Detection of hardcoded API tokens, RSA private keys, SQL injection patterns, and weak crypto (MD5).*

### 📋 Test Prompts:
```text
Scan this code for security vulnerabilities or hardcoded secrets:

public class AppConfig {
    public static final String API_SECRET = "AIzaSyD_98765432101234567890";
    
    public String hashPassword(String pass) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        return new String(md.digest(pass.getBytes()));
    }
}
```

---

## 9. 🚦 Release Readiness Intelligence
*Tests: Subsystem signal aggregation, release gate checks, and GO / NO-GO recommendations.*

### 📋 Test Prompts:
```text
What quality, security, testing, and backup gates should be evaluated before deploying an enterprise application to production? Provide a GO / NO-GO release decision report format.
```

---

## 🤖 10. Autonomous Task Planning & Execution
*Tests: Multi-step goal decomposition into a DAG task graph.*

### 📋 Test Prompts:
```text
Break down the step-by-step task execution plan to migrate a Spring Boot 2.7 application using javax.persistence to Spring Boot 3.2 using jakarta.persistence.
```

---

## 💡 Tips for Best Results in Extension Testing
1. **Source Citations Check**: Look at the bottom of the assistant's answer for `file:line` links (e.g. `[UserService.java](file:///...)`).
2. **Streaming Tokens**: Observe the live word-by-word streaming animation in the Extension UI.
3. **Workspace Switching**: Try selecting different workspace folders in the Extension dropdown and observe how context shifts.
