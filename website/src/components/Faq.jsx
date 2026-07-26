import React, { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';

const FAQS = [
  {
    q: "Does ECIP send any source code to external servers?",
    a: "No. ECIP is a fully self-hosted platform. All repository parsing, vector embedding, BM25 indexing, and LLM inference happen locally on your machine or your own server cluster. There are zero outbound network calls made during normal operation."
  },
  {
    q: "What are the system requirements?",
    a: "ECIP requires Python 3.10+, and Ollama installed and running locally. For LLM inference, we recommend at least 16GB RAM for 7B parameter models. FAISS-based indexing works well on CPU-only machines — no GPU is required, though GPU acceleration is supported."
  },
  {
    q: "Which local LLMs does ECIP support?",
    a: "ECIP works with any model running through Ollama, LM Studio, or any OpenAI-compatible local server. Recommended models include Qwen 2.5 Coder 7B/14B, DeepSeek-Coder-V2, and Llama 3.1. Smaller 3B models also work for machines with limited RAM."
  },
  {
    q: "How does ECIP handle large repositories with thousands of files?",
    a: "ECIP uses SHA-256 checksums during scanning to detect which files have changed since the last index run. Only modified files are re-parsed and re-embedded — unchanged files are skipped entirely. This keeps incremental re-indexing fast even on repositories with 500k+ lines of code."
  },
  {
    q: "Is ECIP free and open-source?",
    a: "Yes. ECIP Lite is released under the MIT open-source license. You are free to use it commercially, fork it, self-host it, and contribute back to the project. There is no SaaS subscription, no freemium tier, and no feature gating."
  },
  {
    q: "What programming languages does ECIP currently support?",
    a: "ECIP v1.x supports Java via the javalang AST parser. The v2.0 roadmap includes full polyglot support for Python, TypeScript, Go, and Rust using Tree-Sitter-based parsers. Generic text chunking is available as a fallback for any file type."
  }
];

export default function Faq() {
  const [open, setOpen] = useState(0);

  return (
    <section id="faq" className="section-gray py-24">
      <div className="max-w-3xl mx-auto px-4 lg:px-8">

        <div className="text-center space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">
            <HelpCircle className="w-3.5 h-3.5" />
            FAQ
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Frequently asked questions
          </h2>
        </div>

        <div className="space-y-3">
          {FAQS.map((f, i) => (
            <div key={i} className="card-float">
              <button
                onClick={() => setOpen(open === i ? -1 : i)}
                className="w-full px-6 py-5 text-left flex items-center justify-between gap-4 cursor-pointer"
              >
                <span className="font-semibold text-gray-900 text-base">{f.q}</span>
                <ChevronDown
                  className={`w-5 h-5 text-gray-400 shrink-0 transition-transform ${open === i ? 'rotate-180 text-indigo-600' : ''}`}
                />
              </button>
              {open === i && (
                <div className="px-6 pb-5 text-sm text-gray-600 leading-relaxed border-t border-gray-50 pt-4">
                  {f.a}
                </div>
              )}
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
