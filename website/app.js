/* ==========================================================================
   ECIP Product Website - Interactive Logic & Simulator Script
   ========================================================================== */

// Demo Presets Data
const DEMO_PRESETS = [
  {
    id: 0,
    title: "Auth & Token Flow",
    question: "How does authentication & token validation work in this project?",
    answer: `The authentication pipeline is managed across 3 primary components:

1. **AuthController.java** (L45-L78): Handles \`POST /api/v1/auth/login\`. Receives credentials and passes them to \`UserService.authenticate()\`.
2. **JwtTokenService.java** (L102-L134): Upon successful authentication, generates a signed JWT payload containing tenant claims, user scopes, and expiration timestamp.
3. **JwtSecurityFilter.java** (L15-L60): Intercepts all incoming HTTP requests, extracts the Bearer token, validates cryptographic signature against local secret key, and injects \`TenantContext\` into the thread-local request state.`,
    ast: `AST Dependency Graph:
  [Class] AuthController
    ├── @RestController
    ├── @Autowired UserService userService
    └── @Autowired JwtTokenService jwtTokenService

  [Class] JwtSecurityFilter extends OncePerRequestFilter
    └── Invocations:
        ├── JwtTokenService.validateToken(String token)
        └── SecurityContextHolder.getContext().setAuthentication(...)`,
    citations: `📄 src/main/java/com/ecip/auth/AuthController.java (Lines 45-78)
📄 src/main/java/com/ecip/auth/JwtTokenService.java (Lines 102-134)
📄 src/main/java/com/ecip/security/JwtSecurityFilter.java (Lines 15-60)`,
    telemetry: `⚡ Retrieval Latency: 14.2 ms
🧠 Intent Analysis: "qa_explain" (Confidence: 0.98)
📦 Retrieved Chunks: 4 (2 Hybrid, 2 AST Method)
🦙 Ollama Model: qwen2.5-coder:7b (Total duration: 840 ms)`
  },
  {
    id: 1,
    title: "Impact Analysis of UserService",
    question: "What classes are impacted if I change UserService method signatures?",
    answer: `Impact Analysis Engine executed downstream dependency graph traversal at depth=3:

Changes to **UserService.java** affect **7 downstream components**:

• **Controllers (Direct Callers):**
  - \`AuthController.java\` (calls \`UserService.login\`, \`UserService.register\`)
  - \`UserController.java\` (calls \`UserService.getProfile\`, \`UserService.updateRole\`)

• **Services & Workers (Indirect Dependencies):**
  - \`AuditLogService.java\` (subscribes to UserCreatedEvent)
  - \`NotificationWorker.java\` (depends on UserDetails payload)

• **Security Rules:**
  - \`RbacPermissionEvaluator.java\` (invokes UserRole resolution)`,
    ast: `Graph Traversal Path:
  UserService (Target Class)
    ├── CALLED_BY ➔ AuthController.java (Line 52)
    ├── CALLED_BY ➔ UserController.java (Line 34, 88)
    ├── DEPENDS_ON ➔ UserRepository.java (Field Injection)
    └── EVENT_BUS ➔ AuditLogService.java (Subscriber)`,
    citations: `📄 src/main/java/com/ecip/service/UserService.java (Target)
📄 src/main/java/com/ecip/controller/AuthController.java
📄 src/main/java/com/ecip/controller/UserController.java`,
    telemetry: `⚡ Graph Traversal Latency: 6.8 ms
🧠 Intent Analysis: "impact_analysis" (Routed directly to Graph Engine)
🌐 Graph Nodes Evaluated: 14 nodes, 22 directed edges
🦙 LLM Summary Latency: 420 ms`
  },
  {
    id: 2,
    title: "Database Schema & Models",
    question: "Where are database tables and Flyway SQL migrations defined?",
    answer: `Database tables and schema migrations are configured in 2 layers:

1. **Flyway SQL Migration Scripts:**
   - \`src/main/resources/db/migration/V1__init_schema.sql\`: Defines \`users\`, \`roles\`, \`permissions\`, and foreign key constraints.
   - \`src/main/resources/db/migration/V2__add_indexes.sql\`: Contains performance indexes on \`users.email\` and \`tenant_id\`.

2. **JPA Entity Models:**
   - \`UserEntity.java\` (mapped to \`users\` table)
   - \`RoleEntity.java\` (mapped to \`roles\` table)`,
    ast: `SQL & JPA Metadata Parsing:
  [SQL Table] users
    ├── Column: id (BIGINT, PRIMARY KEY)
    ├── Column: email (VARCHAR, UNIQUE)
    └── Column: tenant_id (VARCHAR, NOT NULL)

  [JPA Entity] UserEntity.java
    ├── @Table(name = "users")
    └── @OneToMany List<RoleEntity> roles`,
    citations: `📄 src/main/resources/db/migration/V1__init_schema.sql
📄 src/main/java/com/ecip/model/UserEntity.java (Lines 1-65)`,
    telemetry: `⚡ Hybrid Search Latency: 11.5 ms
🧠 Intent Analysis: "schema_lookup" (Exact SQL + Entity match)
📦 Chunks Retrieved: 3 SQL DDL tables, 2 Java Entities`
  },
  {
    id: 3,
    title: "Order Validation Pipeline",
    question: "Where is order validation implemented from controller to database?",
    answer: `The order validation flow proceeds through the following architecture:

1. **OrderController.java** receives \`POST /api/v1/orders\` and calls \`OrderValidator.validate(request)\`.
2. **OrderValidator.java** executes business validation rules:
   - Checks inventory stock availability via \`InventoryService.checkStock()\`.
   - Validates user credit limits via \`CreditLimitEngine.evaluate()\`.
3. **OrderRepository.java** saves approved order entities using \`@Transactional\` database transactions.`,
    ast: `Call Graph Chain:
  OrderController.createOrder()
    ➔ OrderValidator.validate()
        ├── InventoryService.checkStock()
        └── CreditLimitEngine.evaluate()
    ➔ OrderRepository.save()`,
    citations: `📄 src/main/java/com/ecip/order/OrderController.java
📄 src/main/java/com/ecip/order/OrderValidator.java (Lines 22-94)
📄 src/main/java/com/ecip/order/OrderRepository.java`,
    telemetry: `⚡ Retrieval Latency: 18.1 ms
🧠 Intent Analysis: "call_graph_explanation"
📦 Retrieved Chunks: 5 (Method & Call Graph Grounded)`
  }
];

// Pipeline Steps Data
const PIPELINE_NODES = [
  {
    title: "1. Project Scanner",
    desc: "Recursively scans workspace repository files, excluding build artifacts and `.ecip` metadata. Calculates SHA-256 file hashes to support fast incremental re-indexing."
  },
  {
    title: "2. AST Parser",
    desc: "Uses `javalang` (and Tree-Sitter in v2) to extract Abstract Syntax Trees. Maps packages, classes, methods, parameters, annotations, and call graph invocations."
  },
  {
    title: "3. Chunker & Embedder",
    desc: "Splits source code by semantic AST method boundaries. Generates dense vector embeddings using local Ollama embedding models (e.g. `nomic-embed-text`)."
  },
  {
    title: "4. FAISS & BM25 Index",
    desc: "Persists L2 vector embeddings inside persistent FAISS indices and builds an inverted BM25 keyword index for exact symbol lookups."
  },
  {
    title: "5. Intent & Entity Analyzer",
    desc: "Analyzes incoming developer questions using regex patterns and lightweight intent classification to distinguish graph queries (e.g. impact analysis) from semantic code explanation."
  },
  {
    title: "6. Hybrid Retrieval Engine",
    desc: "Executes parallel BM25 keyword matching and FAISS vector similarity search, applying min-max score normalization and cross-encoder re-ranking."
  },
  {
    title: "7. Context Builder",
    desc: "Assembles retrieved code chunks, class signatures, and AST dependency edges into a structured context window without overflowing LLM token budgets."
  },
  {
    title: "8. Local LLM Inference",
    desc: "Sends assembled prompts to your local Ollama LLM instance (Qwen 2.5 Coder, Llama 3) and streams formatted responses with line citations back to the IDE."
  }
];

// Quickstart Commands
const QUICKSTART_COMMANDS = {
  source: `# 1. Clone repository
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ECIP-lite

# 2. Setup virtual environment & dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Pull local model via Ollama
ollama pull qwen2.5-coder:7b

# 4. Start ECIP FastAPI Server
python run_api.py`,

  docker: `# Run ECIP with local GPU support via Docker
docker run -d \\
  --name ecip-server \\
  -p 8000:8000 \\
  -v $(pwd)/workspace:/app/workspace \\
  -v ~/.ollama:/root/.ollama \\
  zadesamir/ecip-lite:latest`,

  vscode: `# Install ECIP VS Code Extension
code --install-extension ecip-lite-1.2.0.vsix

# Open VS Code & Open ECIP Sidebar
# Shift + Cmd + P -> ECIP: Connect Local Server`
};

// Documentation Sections
const DOC_SECTIONS = {
  intro: `
    <h3 style="color: var(--accent-cyan); margin-bottom: 12px;">1. Getting Started with ECIP</h3>
    <p>ECIP (Enterprise Code Intelligence Platform) is an open-source, offline AI assistant designed to run 100% locally on developer machines and enterprise servers.</p>
    <br>
    <h4 style="color: var(--text-main); margin-bottom: 8px;">Key System Prerequisites:</h4>
    <ul>
      <li>Python 3.10+ installed</li>
      <li>Ollama running locally (<code>ollama serve</code>)</li>
      <li>Minimum 8GB RAM (16GB recommended for 7B/14B models)</li>
    </ul>
  `,
  arch: `
    <h3 style="color: var(--accent-cyan); margin-bottom: 12px;">2. System Architecture</h3>
    <p>ECIP separates code understanding into two primary layers:</p>
    <br>
    <ul>
      <li><strong>Deterministic AST Layer:</strong> Parses class inheritance, method signatures, and dependency injection to build call graphs.</li>
      <li><strong>Probabilistic Vector Layer:</strong> Uses FAISS and BM25 to find relevant code snippets based on natural language queries.</li>
    </ul>
  `,
  indexing: `
    <h3 style="color: var(--accent-cyan); margin-bottom: 12px;">3. Indexing Codebases</h3>
    <p>To index a project via CLI or REST API:</p>
    <pre style="background: #060910; padding: 12px; border-radius: 6px; color: var(--accent-cyan); margin-top: 10px;">curl -X POST "http://localhost:8000/api/v1/index" \\
  -H "Content-Type: application/json" \\
  -d '{"project_path": "/path/to/your/project"}'</pre>
  `,
  api: `
    <h3 style="color: var(--accent-cyan); margin-bottom: 12px;">4. REST API Reference</h3>
    <p>ECIP exposes standard REST endpoints:</p>
    <br>
    <ul>
      <li><code>POST /api/v1/query</code> — Submit questions & receive streamed answers</li>
      <li><code>POST /api/v1/index</code> — Trigger background repository indexing</li>
      <li><code>GET /api/v1/workspaces</code> — List active indexed projects</li>
      <li><code>GET /health</code> — System health status</li>
    </ul>
  `,
  ide: `
    <h3 style="color: var(--accent-cyan); margin-bottom: 12px;">5. IDE Setup (VS Code Extension)</h3>
    <p>The ECIP VS Code extension resides in <code>vscode-extension/</code>. Package it using <code>vsce package</code> and install the generated <code>.vsix</code> file directly into VS Code.</p>
  `
};

// Current State Tracking
let currentDemoPreset = 0;
let currentDemoTab = 'answer';

// Initialize Page Controls
document.addEventListener('DOMContentLoaded', () => {
  renderDemoContent();
  selectPipelineNode(0);
  loadDocSection('intro');
});

// Demo Functions
function loadDemoPreset(index) {
  currentDemoPreset = index;
  document.querySelectorAll('.preset-btn').forEach((btn, i) => {
    btn.classList.toggle('active', i === index);
  });
  renderDemoContent();
}

function switchDemoTab(tab) {
  currentDemoTab = tab;
  document.querySelectorAll('.demo-tabs .tab-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tab.toLowerCase()));
  });
  renderDemoContent();
}

function renderDemoContent() {
  const data = DEMO_PRESETS[currentDemoPreset];
  const container = document.getElementById('demo-content-window');
  if (!container) return;

  if (currentDemoTab === 'answer') {
    container.innerHTML = `
      <div style="color: var(--accent-purple); font-weight: 700; margin-bottom: 12px;">Q: "${data.question}"</div>
      <div style="white-space: pre-wrap; line-height: 1.7;">${data.answer}</div>
    `;
  } else if (currentDemoTab === 'ast') {
    container.innerHTML = `<pre style="color: var(--accent-cyan); white-space: pre-wrap;">${data.ast}</pre>`;
  } else if (currentDemoTab === 'citations') {
    container.innerHTML = `<div style="color: var(--accent-emerald); white-space: pre-wrap;">${data.citations}</div>`;
  } else if (currentDemoTab === 'telemetry') {
    container.innerHTML = `<div style="color: var(--accent-amber); white-space: pre-wrap;">${data.telemetry}</div>`;
  }
}

// Pipeline Stepper
function selectPipelineNode(index) {
  const nodeData = PIPELINE_NODES[index];
  document.querySelectorAll('.pipeline-node').forEach((node, i) => {
    node.classList.toggle('active', i === index);
  });
  const box = document.getElementById('pipeline-details-box');
  if (box) {
    box.innerHTML = `
      <h3 style="font-size: 1.35rem; color: var(--accent-purple); margin-bottom: 12px;">${nodeData.title}</h3>
      <p style="font-size: 1.05rem; color: var(--text-muted); line-height: 1.7;">${nodeData.desc}</p>
    `;
  }
}

// Quickstart Switcher
function switchQuickstart(type) {
  const codeEl = document.getElementById('quickstart-code-text');
  if (codeEl && QUICKSTART_COMMANDS[type]) {
    codeEl.textContent = QUICKSTART_COMMANDS[type];
  }
}

function copyQuickstartCode() {
  const codeEl = document.getElementById('quickstart-code-text');
  if (!codeEl) return;
  navigator.clipboard.writeText(codeEl.textContent.trim()).then(() => {
    const copyBtn = document.querySelector('.copy-btn');
    if (copyBtn) {
      copyBtn.textContent = 'Copied! ✓';
      setTimeout(() => { copyBtn.textContent = 'Copy Command'; }, 2000);
    }
  });
}

// FAQ Accordion Toggle
function toggleFaq(element) {
  const parent = element.parentElement;
  parent.classList.toggle('active');
}

// Modals
function openDownloadModal() {
  const modal = document.getElementById('download-modal');
  if (modal) modal.classList.add('active');
}

function closeDownloadModal() {
  const modal = document.getElementById('download-modal');
  if (modal) modal.classList.remove('active');
}

function openDocsModal() {
  const modal = document.getElementById('docs-modal');
  if (modal) modal.classList.add('active');
}

function closeDocsModal() {
  const modal = document.getElementById('docs-modal');
  if (modal) modal.classList.remove('active');
}

function loadDocSection(key) {
  const contentBox = document.getElementById('docs-body-content');
  if (contentBox && DOC_SECTIONS[key]) {
    contentBox.innerHTML = DOC_SECTIONS[key];
  }
}
