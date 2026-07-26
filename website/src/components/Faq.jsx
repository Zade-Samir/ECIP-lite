import React, { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';

const FAQS = [
  {
    q: "Does ECIP send any source code to external cloud servers?",
    a: "No. ECIP is designed specifically for zero-trust and privacy-sensitive codebases. All AST parsing, vector embedding generation, BM25 indexing, and LLM inference run strictly on your local machine or self-hosted server cluster."
  },
  {
    q: "Which local LLMs does ECIP support?",
    a: "ECIP supports any model running on Ollama, LM Studio, or OpenAI-compatible local API servers. Recommended choices include Qwen 2.5 Coder (7B / 14B / 32B), DeepSeek-Coder-V2, and Llama 3.1."
  },
  {
    q: "How does ECIP handle large repositories with thousands of files?",
    a: "ECIP uses SHA-256 hash tracking during project scanning to skip unchanged files. Only modified files are re-parsed and re-embedded, allowing fast incremental index updates even on very large codebases."
  },
  {
    q: "Is ECIP free and open-source?",
    a: "Yes! ECIP Lite is licensed under the permissive MIT Open Source License. You can modify, self-host, and integrate it into commercial products without any restrictions."
  },
  {
    q: "What programming languages does ECIP support?",
    a: "ECIP v1.x supports Java via the javalang AST parser. ECIP v2.0 (planned) will add full polyglot support for Python, TypeScript, Go, and Rust via Tree-Sitter parsers."
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
