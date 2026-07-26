import React, { useState } from 'react';
import { Layers, ArrowRight } from 'lucide-react';

const STEPS = [
  {
    num: "1",
    name: "Project Scanner",
    desc: "Recursively scans workspace repository files, excluding build artifacts and `.ecip` directory. Computes SHA-256 file hashes to support fast incremental re-indexing."
  },
  {
    num: "2",
    name: "AST Parser",
    desc: "Extracts Abstract Syntax Trees using `javalang` (and Tree-Sitter in v2). Maps packages, classes, methods, parameters, annotations, and call graph invocations."
  },
  {
    num: "3",
    name: "Chunker & Embedder",
    desc: "Splits source code by semantic AST method boundaries. Generates dense vector embeddings using local Ollama embedding models (e.g. `nomic-embed-text`)."
  },
  {
    num: "4",
    name: "FAISS & BM25 Index",
    desc: "Persists L2 vector embeddings inside persistent FAISS indices and builds an inverted BM25 keyword index for exact symbol lookups."
  },
  {
    num: "5",
    name: "Intent Analyzer",
    desc: "Analyzes incoming developer questions using regex patterns and lightweight intent classification to distinguish graph queries from semantic code explanation."
  },
  {
    num: "6",
    name: "Hybrid Retrieval",
    desc: "Executes parallel BM25 keyword matching and FAISS vector similarity search, applying min-max score normalization and cross-encoder re-ranking."
  },
  {
    num: "7",
    name: "Context Builder",
    desc: "Assembles retrieved code chunks, class signatures, and AST dependency edges into a structured context window without overflowing LLM token budgets."
  },
  {
    num: "8",
    name: "Local LLM Inference",
    desc: "Sends assembled prompts to your local Ollama LLM instance (Qwen 2.5 Coder, Llama 3) and streams formatted responses with line citations back to the IDE."
  }
];

export default function Pipeline() {
  const [activeStep, setActiveStep] = useState(0);
  const current = STEPS[activeStep];

  return (
    <section id="architecture" className="py-24 bg-[#06080d] border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-semibold uppercase tracking-wider">
            <Layers className="w-3.5 h-3.5" />
            <span>End-to-End Pipeline</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            How ECIP Processes Repository Intelligence
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            Click any step in the pipeline below to inspect its internal mechanics.
          </p>
        </div>

        {/* Stepper Node Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mb-8">
          {STEPS.map((s, idx) => (
            <button
              key={idx}
              onClick={() => setActiveStep(idx)}
              className={`p-3.5 rounded-xl border text-center transition-all cursor-pointer ${
                activeStep === idx
                  ? 'bg-purple-500/20 border-purple-500/50 shadow-lg shadow-purple-500/20 scale-[1.03]'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs mx-auto mb-2 ${
                activeStep === idx ? 'bg-purple-500 text-white' : 'bg-slate-800 text-purple-400'
              }`}>
                {s.num}
              </div>
              <div className="text-[11px] font-bold text-slate-200 truncate">{s.name}</div>
            </button>
          ))}
        </div>

        {/* Selected Step Info Box */}
        <div className="p-8 rounded-2xl bg-[#0b0f19] border border-purple-500/30 shadow-xl space-y-3">
          <div className="text-xs font-mono text-purple-400 font-bold uppercase tracking-wider">
            PIPELINE STAGE {current.num} OF 8
          </div>
          <h3 className="text-2xl font-bold text-white">{current.name}</h3>
          <p className="text-slate-300 text-base leading-relaxed">{current.desc}</p>
        </div>

      </div>
    </section>
  );
}
