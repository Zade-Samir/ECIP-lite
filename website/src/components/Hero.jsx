import React, { useState } from 'react';
import { ShieldCheck, Download, BookOpen, Terminal, Cpu, Database, Network, CheckCircle2 } from 'lucide-react';

function GithubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

export default function Hero({ onOpenDownload, onOpenDocs }) {
  const [activeTab, setActiveTab] = useState('stream');

  return (
    <section className="relative pt-32 pb-20 overflow-hidden bg-gradient-to-b from-[#06080d] via-[#090d16] to-[#06080d]">
      {/* Background Ambient Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Text Content */}
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium tracking-wide">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>100% Offline & Privacy-First Code Intelligence</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.12]">
              Understand your entire codebase.{' '}
              <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-purple-400 bg-clip-text text-transparent">
                Locally. Privately.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-400 leading-relaxed max-w-xl">
              An open-source AI code intelligence platform that parses repository structure, builds AST dependency graphs, and delivers context-aware answers without sending a single byte of code to the cloud.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={onOpenDownload}
                className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-bold text-sm shadow-xl shadow-cyan-500/25 hover:shadow-purple-500/35 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
              >
                <Download className="w-4 h-4" />
                <span>Download ECIP v1.2.0</span>
              </button>

              <a
                href="https://github.com/Zade-Samir/ECIP-lite"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-5 py-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 font-semibold text-sm hover:bg-slate-800 hover:border-slate-700 transition-all"
              >
                <GithubIcon className="w-4 h-4" />
                <span>View Source</span>
              </a>

              <button
                onClick={onOpenDocs}
                className="flex items-center gap-2 px-5 py-3.5 rounded-xl bg-slate-900/50 border border-slate-800/80 text-slate-300 font-semibold text-sm hover:text-white hover:border-slate-700 transition-all cursor-pointer"
              >
                <BookOpen className="w-4 h-4 text-cyan-400" />
                <span>Documentation</span>
              </button>
            </div>

            {/* Micro Feature Indicators */}
            <div className="pt-4 grid grid-cols-3 gap-4 border-t border-slate-800/80 text-xs text-slate-400 font-medium">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Zero Telemetry</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span>FAISS + BM25</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-purple-400" />
                <span>Ollama & GGUF</span>
              </div>
            </div>
          </div>

          {/* Right Live Dashboard Preview Widget */}
          <div className="lg:col-span-6">
            <div className="rounded-2xl bg-[#090d16] border border-cyan-500/30 shadow-2xl shadow-cyan-500/10 overflow-hidden">
              
              {/* Window Header */}
              <div className="bg-[#0f172a] px-4 py-3 border-b border-slate-800/80 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-2 text-xs font-mono text-slate-400">ECIP Interactive Dashboard v1.2</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[11px] font-mono text-emerald-400">OLLAMA ONLINE</span>
                </div>
              </div>

              {/* Sub-Header Live Stats */}
              <div className="grid grid-cols-3 bg-[#0d1322] border-b border-slate-800/80 p-3 text-center text-xs font-mono">
                <div className="border-r border-slate-800/80">
                  <div className="text-slate-500 text-[10px]">PARSED SYMBOLS</div>
                  <div className="text-cyan-400 font-bold">14,280 AST</div>
                </div>
                <div className="border-r border-slate-800/80">
                  <div className="text-slate-500 text-[10px]">FAISS VECTORS</div>
                  <div className="text-purple-400 font-bold">42,500 L2</div>
                </div>
                <div>
                  <div className="text-slate-500 text-[10px]">RETRIEVAL TIME</div>
                  <div className="text-emerald-400 font-bold">14.2 ms</div>
                </div>
              </div>

              {/* Interactive Widget Body */}
              <div className="p-4 space-y-4 font-mono text-xs">
                
                {/* Input Prompt Box */}
                <div className="flex items-center gap-2 bg-[#0f172a] border border-cyan-500/40 rounded-xl px-3.5 py-2.5 text-cyan-300">
                  <span className="text-purple-400 font-bold">Ask ECIP &gt;</span>
                  <span className="text-slate-200">How does authentication & token validation work in this project?</span>
                </div>

                {/* Tab Controls */}
                <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2">
                  <button
                    onClick={() => setActiveTab('stream')}
                    className={`px-3 py-1 rounded-md text-[11px] font-medium transition-all ${
                      activeTab === 'stream'
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    LLM Answer
                  </button>
                  <button
                    onClick={() => setActiveTab('graph')}
                    className={`px-3 py-1 rounded-md text-[11px] font-medium transition-all ${
                      activeTab === 'graph'
                        ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    AST Call Graph
                  </button>
                  <button
                    onClick={() => setActiveTab('citations')}
                    className={`px-3 py-1 rounded-md text-[11px] font-medium transition-all ${
                      activeTab === 'citations'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Citations
                  </button>
                </div>

                {/* Content Box */}
                <div className="bg-[#04060a] border border-slate-800/90 rounded-xl p-4 min-h-[200px] text-slate-300 leading-relaxed overflow-x-auto">
                  {activeTab === 'stream' && (
                    <div className="space-y-2">
                      <div className="text-slate-500 text-[11px] mb-2">[Intent: qa_explain | Extracted Entities: AuthController, TokenService]</div>
                      <p>The authentication pipeline is managed across 3 primary components:</p>
                      <ul className="space-y-1.5 text-slate-300 pl-3 border-l-2 border-cyan-500/40">
                        <li>1. <strong className="text-cyan-400">AuthController.java</strong> (L45-L78): Handles <code className="text-purple-300">POST /api/v1/auth/login</code> and validates credentials.</li>
                        <li>2. <strong className="text-purple-400">JwtProvider.java</strong> (L102-L134): Generates signed JWT payload containing claims & scopes.</li>
                        <li>3. <strong className="text-emerald-400">SecurityFilter.java</strong> (L15-L60): Intercepts Bearer tokens and validates signature locally.</li>
                      </ul>
                    </div>
                  )}

                  {activeTab === 'graph' && (
                    <div className="text-purple-300 font-mono text-[11px] space-y-1">
                      <div>AST Dependency & Call Graph Chain:</div>
                      <div className="pl-2 border-l border-purple-500/40 mt-2 space-y-1">
                        <div>[Class] AuthController</div>
                        <div className="pl-4 text-cyan-400">├── @RestController</div>
                        <div className="pl-4 text-cyan-400">├── @Autowired UserService userService</div>
                        <div className="pl-4 text-cyan-400">└── @Autowired JwtProvider jwtProvider</div>
                        <div className="mt-2">[Invocation Path]</div>
                        <div className="pl-4 text-emerald-400">AuthController.login() ➔ UserService.authenticate() ➔ JwtProvider.createToken()</div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'citations' && (
                    <div className="space-y-2 text-xs">
                      <div className="p-2 rounded-lg bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 flex items-center justify-between">
                        <span>📄 AuthController.java (Lines 45-78)</span>
                        <span className="text-[10px] text-cyan-500">Tier 1 Method Match</span>
                      </div>
                      <div className="p-2 rounded-lg bg-purple-950/40 border border-purple-800/40 text-purple-300 flex items-center justify-between">
                        <span>📄 JwtProvider.java (Lines 102-134)</span>
                        <span className="text-[10px] text-purple-500">Tier 2 Class Match</span>
                      </div>
                      <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-emerald-300 flex items-center justify-between">
                        <span>📄 SecurityFilter.java (Lines 15-60)</span>
                        <span className="text-[10px] text-emerald-500">FAISS Similarity 0.94</span>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
