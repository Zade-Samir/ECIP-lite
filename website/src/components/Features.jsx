import React from 'react';
import { Cpu, Search, GitBranch, Zap, Shield, RefreshCw, Plug, Target } from 'lucide-react';

const FEATURES = [
  {
    icon: <Cpu className="w-5 h-5 text-indigo-600" />,
    bg: "bg-indigo-50",
    title: "Repository Intelligence",
    desc: "Understands multi-file relationships, inheritance trees, and module architecture — not just isolated snippets."
  },
  {
    icon: <Search className="w-5 h-5 text-purple-600" />,
    bg: "bg-purple-50",
    title: "Hybrid Semantic + Lexical Search",
    desc: "Combines dense vector similarity (FAISS) with exact symbol matching (BM25) for high-precision retrieval."
  },
  {
    icon: <GitBranch className="w-5 h-5 text-emerald-600" />,
    bg: "bg-emerald-50",
    title: "AST & Call Graph Analysis",
    desc: "Parses Abstract Syntax Trees to map caller-callee chains, class inheritance, and dependency injection graphs."
  },
  {
    icon: <Zap className="w-5 h-5 text-amber-600" />,
    bg: "bg-amber-50",
    title: "Local LLM Integration",
    desc: "Supports Ollama, Qwen 2.5 Coder, Llama 3, DeepSeek-Coder, and any OpenAI-compatible local server."
  },
  {
    icon: <Shield className="w-5 h-5 text-indigo-600" />,
    bg: "bg-indigo-50",
    title: "Private by Design",
    desc: "Zero external network calls. Runs in air-gapped enterprise environments, defense networks, and high-security settings."
  },
  {
    icon: <RefreshCw className="w-5 h-5 text-cyan-600" />,
    bg: "bg-cyan-50",
    title: "Incremental Re-indexing",
    desc: "SHA-256 hash tracking ensures only modified files are re-indexed — keeping speeds instant on large codebases."
  },
  {
    icon: <Plug className="w-5 h-5 text-emerald-600" />,
    bg: "bg-emerald-50",
    title: "IDE Extensions",
    desc: "Seamless VS Code and IntelliJ IDEA sidebar integrations with inline citations and file-jump support."
  },
  {
    icon: <Target className="w-5 h-5 text-rose-600" />,
    bg: "bg-rose-50",
    title: "Impact Analysis Engine",
    desc: "Traverses downstream dependency graphs to predict breaking changes before refactoring across enterprise services."
  },
];

export default function Features() {
  return (
    <section id="features" className="section-gray py-24">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">

        <div className="text-center max-w-2xl mx-auto space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">Capabilities</div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Engineered for enterprise codebases
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            Advanced code intelligence features built for large-scale repositories with thousands of files.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map((f, idx) => (
            <div key={idx} className="feature-card">
              <div className={`w-10 h-10 rounded-xl ${f.bg} flex items-center justify-center mb-4`}>
                {f.icon}
              </div>
              <h3 className="font-bold text-gray-900 mb-2 text-[15px]">{f.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
