import React, { useState } from 'react';
import { Download, BookOpen, ArrowRight, ShieldCheck, Zap, Lock, CheckCircle2 } from 'lucide-react';

function GithubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

const LOGOS = [
  { name: "Ollama", emoji: "🦙" },
  { name: "VS Code", emoji: "💙" },
  { name: "IntelliJ", emoji: "🛠️" },
  { name: "GitHub", emoji: "🐙" },
  { name: "Qwen 2.5", emoji: "🤖" },
  { name: "Llama 3", emoji: "🦙" },
];

export default function Hero({ onOpenDownload, onOpenDocs }) {
  const [activeTab, setActiveTab] = useState('stream');

  return (
    <section className="section-light pt-28 pb-8 relative overflow-hidden">
      {/* Soft background gradient blob */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-b from-indigo-50 via-white to-transparent rounded-full blur-3xl opacity-70" />
      </div>

      <div className="max-w-7xl mx-auto px-4 lg:px-8 relative">
        
        {/* Centered Hero Text */}
        <div className="text-center max-w-4xl mx-auto space-y-6 mb-12">

          {/* Badge */}
          <div className="inline-flex items-center gap-2 hero-badge">
            <ShieldCheck className="w-3.5 h-3.5 text-green-600" />
            <span>100% Offline &amp; Private — No Cloud Required</span>
          </div>

          {/* Headline */}
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-gray-900 tracking-tight leading-[1.08]">
            Your entire codebase.{' '}
            <span className="text-indigo-600">Understood.</span>
            {' '}Privately.
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-gray-500 leading-relaxed max-w-2xl mx-auto font-normal">
            An open-source AI code intelligence platform that indexes your entire repository, builds AST dependency graphs, and delivers contextual answers — all running locally on your machine.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button onClick={onOpenDownload} className="btn-primary text-base">
              <Download className="w-4 h-4" />
              Download ECIP — Free
            </button>
            <a
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-outline text-base"
            >
              <GithubIcon className="w-4 h-4" />
              View on GitHub
            </a>
            <button onClick={onOpenDocs} className="btn-outline text-base">
              <BookOpen className="w-4 h-4 text-indigo-500" />
              Documentation
            </button>
          </div>

          {/* Trust Badges */}
          <div className="flex flex-wrap items-center justify-center gap-5 pt-2 text-xs text-gray-400 font-medium">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-green-500" />Zero Data Egress</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-green-500" />MIT License</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-green-500" />FAISS + BM25</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-green-500" />Works with Ollama</span>
          </div>
        </div>

        {/* Floating Product Screenshot Card */}
        <div className="card-float max-w-5xl mx-auto">
          {/* Window Chrome */}
          <div className="bg-gray-100 border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-400" />
              <span className="w-3 h-3 rounded-full bg-amber-400" />
              <span className="w-3 h-3 rounded-full bg-green-400" />
              <span className="ml-3 text-xs font-mono text-gray-500">ECIP — Enterprise Code Intelligence Dashboard v1.2</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-[10px] font-mono text-green-600 font-semibold">OLLAMA RUNNING</span>
            </div>
          </div>

          {/* Stats Sub-Header */}
          <div className="grid grid-cols-3 border-b border-gray-100 bg-white">
            <div className="p-3 text-center border-r border-gray-100">
              <div className="text-[10px] text-gray-400 font-mono uppercase">PARSED SYMBOLS</div>
              <div className="text-indigo-600 font-extrabold font-mono text-lg">14,280 AST</div>
            </div>
            <div className="p-3 text-center border-r border-gray-100">
              <div className="text-[10px] text-gray-400 font-mono uppercase">FAISS VECTORS</div>
              <div className="text-indigo-600 font-extrabold font-mono text-lg">42,500 L2</div>
            </div>
            <div className="p-3 text-center">
              <div className="text-[10px] text-gray-400 font-mono uppercase">RETRIEVAL TIME</div>
              <div className="text-emerald-600 font-extrabold font-mono text-lg">14.2 ms</div>
            </div>
          </div>

          {/* Interactive Panel */}
          <div className="bg-gray-50 p-5 space-y-4">
            {/* Query Input */}
            <div className="flex items-center gap-2.5 bg-white border border-indigo-200 rounded-xl px-4 py-3 text-sm shadow-sm">
              <span className="text-indigo-400 font-mono font-bold text-xs">Ask ECIP &gt;</span>
              <span className="text-gray-700 font-medium">How does authentication &amp; token validation work?</span>
            </div>

            {/* Output Tabs */}
            <div className="flex items-center gap-1 border-b border-gray-200 pb-2">
              {[['stream','LLM Answer'],['graph','AST Graph'],['citations','Citations (3)']].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeTab === key
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Output Content */}
            <div className="bg-white border border-gray-100 rounded-xl p-4 min-h-[180px] text-sm text-gray-700 leading-relaxed shadow-sm overflow-x-auto font-mono">
              {activeTab === 'stream' && (
                <div className="space-y-2 text-xs">
                  <div className="text-gray-400 text-[11px]">[Intent: qa_explain | Entities: AuthController, JwtTokenService]</div>
                  <p className="text-gray-800 font-sans text-sm leading-relaxed">The authentication pipeline is managed across 3 components:</p>
                  <ul className="border-l-2 border-indigo-300 pl-4 space-y-1.5 text-gray-700">
                    <li>1. <strong className="text-indigo-600">AuthController.java</strong> (L45-78): Handles <code className="bg-gray-100 px-1 rounded">POST /api/v1/auth/login</code></li>
                    <li>2. <strong className="text-purple-600">JwtProvider.java</strong> (L102-134): Generates signed JWT payload with claims</li>
                    <li>3. <strong className="text-emerald-600">SecurityFilter.java</strong> (L15-60): Validates Bearer tokens locally</li>
                  </ul>
                </div>
              )}
              {activeTab === 'graph' && (
                <pre className="text-indigo-700 text-[11px] leading-relaxed">{`[Class] AuthController
  ├── @RestController
  ├── @Autowired UserService userService
  └── @Autowired JwtProvider jwtProvider

[Call Chain]
  AuthController.login()
    ➔ UserService.authenticate()
    ➔ JwtProvider.createToken()`}</pre>
              )}
              {activeTab === 'citations' && (
                <div className="space-y-2">
                  <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-100 text-xs text-indigo-700 flex justify-between">
                    <span>📄 AuthController.java (Lines 45-78)</span>
                    <span className="text-indigo-400">FAISS Tier 1</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-purple-50 border border-purple-100 text-xs text-purple-700 flex justify-between">
                    <span>📄 JwtProvider.java (Lines 102-134)</span>
                    <span className="text-purple-400">BM25 Match</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-100 text-xs text-emerald-700 flex justify-between">
                    <span>📄 SecurityFilter.java (Lines 15-60)</span>
                    <span className="text-emerald-400">Vector 0.94</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Social Proof Logo Strip */}
        <div className="mt-12 text-center">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-widest mb-5">Works with your stack</p>
          <div className="flex flex-wrap items-center justify-center gap-6">
            {LOGOS.map((l) => (
              <div key={l.name} className="flex items-center gap-2 text-sm text-gray-500 font-semibold hover:text-gray-800 transition-colors">
                <span className="text-xl">{l.emoji}</span>
                <span>{l.name}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  );
}
