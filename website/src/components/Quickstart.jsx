import React, { useState } from 'react';
import { Terminal, Copy, Check } from 'lucide-react';

const TABS = {
  source: {
    label: "Source Install",
    code: `# 1. Clone ECIP repository
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ECIP-lite

# 2. Setup Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Pull local LLM via Ollama
ollama pull qwen2.5-coder:7b

# 4. Launch ECIP API Server
python run_api.py`
  },
  docker: {
    label: "Docker",
    code: `docker run -d \\
  --name ecip-server \\
  -p 8000:8000 \\
  -v $(pwd)/workspace:/app/workspace \\
  -v ~/.ollama:/root/.ollama \\
  zadesamir/ecip-lite:latest`
  },
  vscode: {
    label: "VS Code",
    code: `# Install ECIP VS Code Extension
code --install-extension ecip-lite-1.2.0.vsix

# Open VS Code → Ctrl+Shift+P
# Execute: ECIP: Connect to Local Server`
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
            Up and running in 60 seconds
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            Choose your installation method below.
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
