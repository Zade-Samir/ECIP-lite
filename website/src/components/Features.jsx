import React from 'react';
import { Cpu, Search, GitBranch, Shield, Zap, RefreshCw, Plug, Target } from 'lucide-react';

export default function Features() {
  const features = [
    {
      icon: <Cpu className="w-6 h-6 text-cyan-400" />,
      title: "Repository Intelligence",
      desc: "Understands multi-file relationships, inheritance trees, and module architecture instead of isolating single file snippets."
    },
    {
      icon: <Search className="w-6 h-6 text-purple-400" />,
      title: "Hybrid Semantic + Lexical Search",
      desc: "Combines dense vector similarity (FAISS) with exact symbol matching (BM25) for high-precision retrieval."
    },
    {
      icon: <GitBranch className="w-6 h-6 text-emerald-400" />,
      title: "AST & Dependency Graphs",
      desc: "Parses Abstract Syntax Trees to map caller/callee method links, class inheritance, and dependency injection."
    },
    {
      icon: <Zap className="w-6 h-6 text-amber-400" />,
      title: "Local LLMs Integration",
      desc: "Native support for Ollama, Qwen 2.5, Llama 3, DeepSeek-Coder, and OpenAI-compatible local servers."
    },
    {
      icon: <Shield className="w-6 h-6 text-cyan-400" />,
      title: "Private by Design",
      desc: "Zero external network telemetry. Operates seamlessly in air-gapped, defense, and high-security enterprise environments."
    },
    {
      icon: <RefreshCw className="w-6 h-6 text-purple-400" />,
      title: "Incremental Indexing",
      desc: "SHA-256 hash tracking re-indexes only modified files, saving computing power and maintaining instant query speed."
    },
    {
      icon: <Plug className="w-6 h-6 text-emerald-400" />,
      title: "IDE Extensions",
      desc: "Seamless integration with VS Code and IntelliJ IDEA sidebar views with inline citations and file jumping."
    },
    {
      icon: <Target className="w-6 h-6 text-amber-400" />,
      title: "Impact Analysis Engine",
      desc: "Predicts downstream class breaking changes before refactoring code across large enterprise services."
    }
  ];

  return (
    <section id="features" className="py-24 bg-[#080c14] relative">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <span>Capabilities</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Engineered for Enterprise Codebases
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            Advanced code intelligence features built specifically for large-scale enterprise repositories.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, idx) => (
            <div
              key={idx}
              className="glass-panel p-6 rounded-2xl border border-slate-800 hover:border-cyan-500/40 glass-card-hover space-y-3"
            >
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 inline-block">
                {f.icon}
              </div>
              <h3 className="text-lg font-bold text-white">{f.title}</h3>
              <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
