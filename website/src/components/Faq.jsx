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
    a: "ECIP uses SHA-256 hash tracking during project scanning to skip unchanged files. Only modified files are re-parsed and re-embedded, allowing fast incremental index updates."
  },
  {
    q: "Is ECIP free and open-source?",
    a: "Yes! ECIP Lite is licensed under the permissive MIT Open Source License. You can modify, self-host, and integrate it into commercial products without restrictions."
  }
];

export default function Faq() {
  const [openIdx, setOpenIdx] = useState(0);

  return (
    <section id="faq" className="py-24 bg-[#080c14] border-t border-slate-800/80">
      <div className="max-w-4xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>FAQ</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="space-y-4">
          {FAQS.map((f, idx) => (
            <div
              key={idx}
              className="rounded-2xl bg-[#0a0f1d] border border-slate-800 overflow-hidden transition-all"
            >
              <button
                onClick={() => setOpenIdx(openIdx === idx ? -1 : idx)}
                className="w-full p-5 text-left font-bold text-sm sm:text-base text-slate-200 flex items-center justify-between cursor-pointer hover:text-cyan-300"
              >
                <span>{f.q}</span>
                <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${openIdx === idx ? 'rotate-180 text-cyan-400' : ''}`} />
              </button>

              {openIdx === idx && (
                <div className="px-5 pb-5 text-xs sm:text-sm text-slate-400 leading-relaxed border-t border-slate-800/60 pt-3">
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
