import React, { useState } from 'react';
import { Terminal, Copy, Check } from 'lucide-react';

const TABS = {
  source: {
    label: "Source Install",
    code: `# Clone the repository
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ECIP-lite

# Create a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Pull your preferred LLM via Ollama
ollama pull qwen2.5-coder:7b

# Start the ECIP server
python run_api.py
# API now running at: http://localhost:8000`
  },
  docker: {
    label: "Docker",
    code: `# Pull and run ECIP as a Docker container
# Ollama must be running on the host machine

docker run -d \\
  --name ecip \\
  -p 8000:8000 \\
  -v $(pwd)/workspace:/workspace \\
  -e OLLAMA_HOST=http://host.docker.internal:11434 \\
  ghcr.io/zade-samir/ecip-lite:latest

# API available at: http://localhost:8000`
  },
  vscode: {
    label: "VS Code Extension",
    code: `# Step 1: Start ECIP server (see Source Install tab)
python run_api.py

# Step 2: Install the VS Code extension
code --install-extension ecip-lite-1.2.0.vsix

# Step 3: Connect in VS Code
# Press Ctrl+Shift+P (or Cmd+Shift+P on macOS)
# Run: "ECIP: Connect to Local Server"
# Enter server URL: http://localhost:8000`
  }
};

export default function Quickstart() {
  const [tab, setTab] = useState('source');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(TABS[tab].code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="quickstart" className="section-indigo py-24">
      <div className="max-w-5xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-2xl mx-auto space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">
            <Terminal className="w-3.5 h-3.5" />
            Developer Quickstart
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            From zero to running in under 5 minutes
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            Choose your preferred installation method. Requires Python 3.10+ and Ollama installed on your machine.
          </p>
        </div>

        <div className="terminal-card">
          {/* Tab Header */}
          <div className="flex items-center justify-between bg-gray-900 border-b border-gray-800 px-5 py-3">
            <div className="flex items-center gap-1.5">
              {Object.entries(TABS).map(([key, { label }]) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    tab === key
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 text-xs hover:bg-gray-700 transition-all cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
          </div>

          {/* Code Block */}
          <div className="p-6 font-mono text-sm text-gray-200 leading-loose overflow-x-auto">
            <pre>{TABS[tab].code}</pre>
          </div>
        </div>

      </div>
    </section>
  );
}
