/* ==========================================================================
   ECIP Visual Website - Chaicode Inspired Interactive Script
   Includes Hero Stepper, Approach Leap Metric Gauges & Planner Grid
   ========================================================================== */

// 1. Hero Step-by-Step Visualizer Data
const HERO_STEPS = [
  {
    astPos: '10%',
    vecPos: '80%',
    activeChunk: 0,
    matchedChunk: -1,
    desc: 'Step 1: User query "How does authentication work?" received. AST Parser scans package AuthController.'
  },
  {
    astPos: '30%',
    vecPos: '60%',
    activeChunk: 1,
    matchedChunk: -1,
    desc: 'Step 2: AST Parser extracts constructor dependency UserService. FAISS vector search retrieves relevant embeddings.'
  },
  {
    astPos: '50%',
    vecPos: '50%',
    activeChunk: 2,
    matchedChunk: 2,
    desc: 'Step 3: Exact match on JwtTokenService.java! Score Fusion merges BM25 score (1.0) and FAISS L2 similarity.'
  },
  {
    astPos: '70%',
    vecPos: '70%',
    activeChunk: 3,
    matchedChunk: 3,
    desc: 'Step 4: AST Call Graph grounds JwtSecurityFilter.java invocations. Context assembled for Local Ollama LLM.'
  },
  {
    astPos: '90%',
    vecPos: '90%',
    activeChunk: 4,
    matchedChunk: 4,
    desc: 'Step 5: Ollama streams token response with line citations [AuthController.java:L45-L78]. Execution complete!'
  }
];

let heroStepIndex = 0;
let heroPlayInterval = null;
let isPlaying = true;

// 2. Approach Leap Data (Brute Force -> Better)
const APPROACHES_DATA = [
  {
    time: "O(N) Naive Scan",
    timeColor: "var(--accent-rose)",
    precision: "25%",
    precisionColor: "var(--accent-rose)",
    risk: "HIGH",
    riskColor: "var(--accent-rose)",
    ops: "1,000,000 text operations",
    progress: 25,
    desc: "Naive text chunking splits files every 500 characters, severing class headers from method bodies and injecting massive noise into the LLM context."
  },
  {
    time: "O(log N) Vector Search",
    timeColor: "var(--accent-amber)",
    precision: "65%",
    precisionColor: "var(--accent-amber)",
    risk: "MEDIUM",
    riskColor: "var(--accent-amber)",
    ops: "15,000 vector comparisons",
    progress: 65,
    desc: "Pure vector search finds semantically similar text snippets, but lacks class dependency edges and fails on exact camelCase method names."
  },
  {
    time: "O(1) AST Graph + FAISS",
    timeColor: "var(--accent-emerald)",
    precision: "98%",
    precisionColor: "var(--accent-emerald)",
    risk: "LOW",
    riskColor: "var(--accent-emerald)",
    ops: "42 direct AST graph hops",
    progress: 98,
    desc: "ECIP Hybrid Grounding combines deterministic AST symbol links with FAISS vector search and BM25 exact matching for 100% accurate code answers."
  }
];

// 3. Planner Data (Schedule / Capacity)
let plannerState = {
  repo: 'medium',
  mode: 'incremental',
  threads: 8
};

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
    <h3 style="color: var(--accent-cyan); margin-bottom: 12px;">1. Getting Started with ECIP Visual</h3>
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

// Initialize Page Controls
document.addEventListener('DOMContentLoaded', () => {
  renderHeroStep();
  startHeroAutoPlay();
  selectApproach(0);
  renderPlannerMatrix();
  loadDocSection('intro');
});

// Hero Stepper Functions
function renderHeroStep() {
  const step = HERO_STEPS[heroStepIndex];
  const pointerAST = document.getElementById('pointer-ast');
  const pointerVec = document.getElementById('pointer-vector');
  const descEl = document.getElementById('hero-step-description');

  if (pointerAST) pointerAST.style.left = step.astPos;
  if (pointerVec) pointerVec.style.left = step.vecPos;
  if (descEl) descEl.textContent = step.desc;

  // Highlight Chunk Boxes
  for (let i = 0; i < 5; i++) {
    const chunkBox = document.getElementById(`chunk-${i}`);
    if (!chunkBox) continue;
    chunkBox.classList.remove('active', 'matched');
    if (i === step.activeChunk) chunkBox.classList.add('active');
    if (i === step.matchedChunk) chunkBox.classList.add('matched');
  }
}

function stepVisualizer(direction) {
  heroStepIndex = (heroStepIndex + direction + HERO_STEPS.length) % HERO_STEPS.length;
  renderHeroStep();
}

function togglePlayVisualizer() {
  const btn = document.getElementById('play-btn');
  if (isPlaying) {
    clearInterval(heroPlayInterval);
    isPlaying = false;
    if (btn) btn.textContent = '▶ Play';
  } else {
    startHeroAutoPlay();
    isPlaying = true;
    if (btn) btn.textContent = '❚❚ Pause';
  }
}

function startHeroAutoPlay() {
  clearInterval(heroPlayInterval);
  heroPlayInterval = setInterval(() => {
    stepVisualizer(1);
  }, 2500);
}

// Approach Leap Functions
function selectApproach(index) {
  const data = APPROACHES_DATA[index];
  document.querySelectorAll('.approach-tab-btn').forEach((btn, i) => {
    btn.classList.toggle('active', i === index);
  });

  const timeVal = document.getElementById('approach-time-val');
  const precVal = document.getElementById('approach-precision-val');
  const riskVal = document.getElementById('approach-risk-val');
  const opsVal = document.getElementById('approach-ops-count');
  const progress = document.getElementById('approach-progress-bar');
  const desc = document.getElementById('approach-desc-text');

  if (timeVal) { timeVal.textContent = data.time; timeVal.style.color = data.timeColor; }
  if (precVal) { precVal.textContent = data.precision; precVal.style.color = data.precisionColor; }
  if (riskVal) { riskVal.textContent = data.risk; riskVal.style.color = data.riskColor; }
  if (opsVal) opsVal.textContent = data.ops;
  if (progress) progress.style.width = `${data.progress}%`;
  if (desc) desc.textContent = data.desc;
}

// Planner Functions
function updatePlanner(type, value) {
  plannerState[type] = value;
  
  // Highlight buttons
  const group = event.target.parentElement;
  group.querySelectorAll('.planner-opt-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');

  renderPlannerMatrix();
}

function renderPlannerMatrix() {
  const grid = document.getElementById('planner-matrix-grid');
  const estText = document.getElementById('planner-est-time');
  const chunksText = document.getElementById('planner-chunks-text');
  if (!grid) return;

  grid.innerHTML = '';
  let count = 14;
  if (plannerState.repo === 'small') count = 14;
  else if (plannerState.repo === 'medium') count = 28;
  else if (plannerState.repo === 'enterprise') count = 42;

  let activeCount = plannerState.mode === 'incremental' ? Math.floor(count * 0.3) : count;
  if (activeCount === 0) activeCount = 3;

  for (let i = 1; i <= count; i++) {
    const cell = document.createElement('div');
    cell.className = 'matrix-cell' + (i <= activeCount ? ' done' : '');
    cell.textContent = i;
    grid.appendChild(cell);
  }

  let timeEst = (activeCount * 0.04 / (plannerState.threads / 4)).toFixed(1);
  if (estText) {
    estText.textContent = `Estimated Build Time: ~${timeEst} seconds (${plannerState.mode === 'incremental' ? 'Incremental Hash' : 'Full Clean'})`;
  }
  if (chunksText) {
    chunksText.textContent = `${activeCount} / ${count} AST Chunks Synced · 100% Complete`;
  }
}

// Quickstart Switcher
function switchQuickstart(type) {
  const codeEl = document.getElementById('quickstart-code-text');
  if (codeEl && QUICKSTART_COMMANDS[type]) {
    codeEl.textContent = QUICKSTART_COMMANDS[type];
  }
  
  document.querySelectorAll('#quickstart .approach-tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  event.target.classList.add('active');
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
