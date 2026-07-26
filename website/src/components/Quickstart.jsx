import React, { useState } from 'react';
import { Terminal, Copy, Check } from 'lucide-react';

const COMMANDS = {
  source: `# 1. Clone ECIP repository
git clone https://github.com/Zade-Samir/ECIP-lite.git
cd ECIP-lite

# 2. Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Pull local LLM via Ollama
ollama pull qwen2.5-coder:7b

# 4. Launch ECIP API Server
python run_api.py`,

  docker: `# Run ECIP Docker container with local Ollama mounting
docker run -d \\
  --name ecip-server \\
  -p 8000:8000 \\
  -v $(pwd)/workspace:/app/workspace \\
  -v ~/.ollama:/root/.ollama \\
  zadesamir/ecip-lite:latest`,

  vscode: `# Install ECIP VS Code Extension
code --install-extension ecip-lite-1.2.0.vsix

# Open VS Code -> Press Ctrl+Shift+P
# Execute: ECIP: Connect Local Server`
};

export default function Quickstart() {
  const [tab, setTab] = useState('source');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(COMMANDS[tab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="quickstart" className="py-24 bg-[#080c14] relative">
      <div className="max-w-5xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-12">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <Terminal className="w-3.5 h-3.5" />
            <span>Developer Onboarding</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Get Up and Running in 60 Seconds
          </h2>
        </div>

        <div className="rounded-2xl border border-cyan-500/30 bg-[#090d16] overflow-hidden shadow-2xl p-6 space-y-4">
          
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setTab('source')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  tab === 'source' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Source Install
              </button>
              <button
                onClick={() => setTab('docker')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  tab === 'docker' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Docker Container
              </button>
              <button
                onClick={() => setTab('vscode')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  tab === 'vscode' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                VS Code Extension
              </button>
            </div>

            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 text-xs hover:bg-slate-700 transition-all cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-cyan-400" />}
              <span>{copied ? 'Copied!' : 'Copy Code'}</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-[#04060a] border border-slate-800 font-mono text-xs text-slate-200 leading-relaxed overflow-x-auto">
            <pre>{COMMANDS[tab]}</pre>
          </div>

        </div>

      </div>
    </section>
  );
}
