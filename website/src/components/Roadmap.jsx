import React from 'react';
import { GitCommit, CheckCircle2, Clock, Sparkles } from 'lucide-react';

const VERSIONS = [
  {
    ver: "v1.0",
    label: "Launched",
    color: "bg-emerald-50 border-emerald-200 text-emerald-700",
    dot: "bg-emerald-500",
    items: [
      "Java AST parsing & metadata extraction",
      "FAISS vector index persistence",
      "Ollama local LLM integration",
      "Streamed REST API & CLI responses",
    ]
  },
  {
    ver: "v1.5",
    label: "In Progress",
    color: "bg-indigo-50 border-indigo-200 text-indigo-700",
    dot: "bg-indigo-500",
    items: [
      "VS Code Extension Sidebar",
      "IntelliJ IDEA Plugin",
      "SHA-256 incremental hash tracking",
      "Cross-Encoder Re-ranking",
    ]
  },
  {
    ver: "v2.0",
    label: "Planned",
    color: "bg-gray-100 border-gray-200 text-gray-500",
    dot: "bg-gray-400",
    items: [
      "Tree-Sitter Polyglot AST (Python, TS, Go, Rust)",
      "SQLite-vec migration (sqlite-vec)",
      "1-Hop Graph Context Expansion",
      "Multi-repository impact reasoning",
    ]
  }
];

export default function Roadmap() {
  return (
    <section id="roadmap" className="section-light py-24">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">

        <div className="text-center max-w-2xl mx-auto space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">
            <Sparkles className="w-3.5 h-3.5" />
            Public Roadmap
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            The evolution of ECIP
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            A transparent, community-driven roadmap for the platform.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {VERSIONS.map((v, i) => (
            <div key={i} className="feature-card space-y-4">
              <div className="flex items-center justify-between">
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-bold ${v.color}`}>
                  <span className={`w-2 h-2 rounded-full ${v.dot}`} />
                  {v.ver} — {v.label}
                </div>
              </div>
              <ul className="space-y-2.5">
                {v.items.map((item, j) => (
                  <li key={j} className="flex items-start gap-2.5 text-sm text-gray-600">
                    <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
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
