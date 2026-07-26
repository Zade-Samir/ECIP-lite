import React, { useState } from 'react';
import { Layers } from 'lucide-react';

const STEPS = [
  { num: "01", name: "Project Scanner", desc: "Recursively scans workspace files, skipping build artifacts. Computes SHA-256 hashes for fast incremental re-indexing." },
  { num: "02", name: "AST Parser", desc: "Extracts Abstract Syntax Trees using javalang (and Tree-Sitter in v2). Maps classes, methods, parameters, and call chains." },
  { num: "03", name: "Chunker & Embedder", desc: "Splits code by semantic AST method boundaries. Generates dense vector embeddings using local Ollama embedding models." },
  { num: "04", name: "FAISS & BM25 Index", desc: "Persists L2 vector embeddings in persistent FAISS indices and builds an inverted BM25 keyword index for exact symbol lookups." },
  { num: "05", name: "Intent Analyzer", desc: "Classifies incoming questions using regex patterns and lightweight intent classification to route to the correct engine." },
  { num: "06", name: "Hybrid Retrieval", desc: "Executes parallel BM25 keyword matching and FAISS vector similarity search, then applies cross-encoder re-ranking." },
  { num: "07", name: "Context Builder", desc: "Assembles retrieved code chunks, class signatures, and AST dependency edges within the LLM context window budget." },
  { num: "08", name: "Local LLM Inference", desc: "Sends assembled prompts to your local Ollama instance and streams formatted responses with file citations back to the IDE." },
];

export default function Pipeline() {
  const [active, setActive] = useState(0);

  return (
    <section id="architecture" className="section-gray py-24">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">

        <div className="text-center max-w-2xl mx-auto space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">
            <Layers className="w-3.5 h-3.5" />
            End-to-End Pipeline
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            How ECIP processes repository intelligence
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            Click any step to inspect the internal mechanics of each pipeline stage.
          </p>
        </div>

        {/* Step Nodes Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mb-8">
          {STEPS.map((s, idx) => (
            <button
              key={idx}
              onClick={() => setActive(idx)}
              className={`p-3.5 rounded-2xl border text-center transition-all cursor-pointer ${
                active === idx
                  ? 'bg-indigo-600 border-indigo-600 text-white shadow-lg shadow-indigo-200'
                  : 'bg-white border-gray-200 hover:border-indigo-300 text-gray-700'
              }`}
            >
              <div className={`w-7 h-7 rounded-full flex items-center justify-center font-extrabold text-xs mx-auto mb-2 ${
                active === idx ? 'bg-white/20 text-white' : 'bg-indigo-50 text-indigo-600'
              }`}>
                {s.num}
              </div>
              <div className="text-[11px] font-bold truncate">{s.name}</div>
            </button>
          ))}
        </div>

        {/* Active Step Description */}
        <div className="card-float p-8 max-w-3xl mx-auto">
          <div className="text-xs font-mono font-bold text-indigo-400 uppercase tracking-wider mb-2">
            PIPELINE STAGE {STEPS[active].num} OF 08
          </div>
          <h3 className="text-2xl font-extrabold text-gray-900 mb-3">{STEPS[active].name}</h3>
          <p className="text-gray-600 text-base leading-relaxed">{STEPS[active].desc}</p>
        </div>

      </div>
    </section>
  );
}
