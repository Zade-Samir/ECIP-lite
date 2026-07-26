import React from 'react';
import { GitCommit, Sparkles, CheckCircle2, Clock } from 'lucide-react';

export default function Roadmap() {
  const versions = [
    {
      ver: "v1.0 — Launched (Core RAG)",
      status: "COMPLETED",
      badgeClass: "bg-emerald-500/15 border-emerald-500/40 text-emerald-400",
      items: [
        "Java AST parsing & metadata extraction",
        "FAISS vector index persistence",
        "Ollama local LLM integration",
        "Streamed API & CLI responses"
      ]
    },
    {
      ver: "v1.5 — In Progress",
      status: "IN PROGRESS",
      badgeClass: "bg-cyan-500/15 border-cyan-500/40 text-cyan-400",
      items: [
        "VS Code Extension Sidebar",
        "IntelliJ IDEA Plugin",
        "Incremental SHA-256 hash tracking",
        "Cross-Encoder Reranking"
      ]
    },
    {
      ver: "v2.0 — Planned",
      status: "PLANNED",
      badgeClass: "bg-purple-500/15 border-purple-500/40 text-purple-400",
      items: [
        "Tree-Sitter Polyglot AST (Python, TS, Go, Rust)",
        "SQLite Vector (sqlite-vec) migration",
        "1-Hop Graph Context Expansion",
        "Multi-repository impact reasoning"
      ]
    }
  ];

  return (
    <section id="roadmap" className="py-24 bg-[#06080d] border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Public Roadmap</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            The Evolution of ECIP Platform
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {versions.map((v, idx) => (
            <div key={idx} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
              <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${v.badgeClass}`}>
                <GitCommit className="w-3.5 h-3.5" />
                <span>{v.ver}</span>
              </div>

              <ul className="space-y-2 text-xs sm:text-sm text-slate-300">
                {v.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
