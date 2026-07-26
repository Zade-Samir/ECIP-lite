import React, { useState } from 'react';
import { Layers } from 'lucide-react';

const STEPS = [
  { num: "01", name: "Project Scanner", desc: "ECIP recursively walks your repository, identifying source files and computing SHA-256 checksums. Only changed files are re-processed on subsequent runs, making updates near-instant." },
  { num: "02", name: "AST Parser", desc: "Each source file is parsed into an Abstract Syntax Tree. ECIP extracts classes, methods, annotations, field declarations, and caller-callee relationships into a structured knowledge graph." },
  { num: "03", name: "Chunker & Embedder", desc: "Code is split at natural AST boundaries (per method, per class). Each chunk is converted into a numerical vector embedding using a locally-running Ollama embedding model." },
  { num: "04", name: "Vector & Keyword Index", desc: "Embeddings are stored in a persistent FAISS index for semantic search. A BM25 inverted index is built in parallel for exact symbol and keyword lookups." },
  { num: "05", name: "Intent Classifier", desc: "When you ask a question, ECIP classifies your intent — distinguishing between \"explain this code\", \"find usages\", \"impact analysis\", and \"schema lookup\" to route to the right engine." },
  { num: "06", name: "Hybrid Retrieval", desc: "BM25 and FAISS searches run in parallel. Results are merged, deduplicated, and re-ranked by relevance score to produce the most precise set of context chunks." },
  { num: "07", name: "Context Assembly", desc: "Retrieved code chunks, class signatures, and dependency edges are assembled into a structured prompt that fits within the LLM context window without truncation." },
  { num: "08", name: "LLM Response", desc: "The assembled prompt is sent to your local Ollama instance. The response streams directly to your IDE or API client, with source file citations referencing exact line numbers." },
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
