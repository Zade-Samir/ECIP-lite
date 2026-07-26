import React from 'react';
import { Check, X } from 'lucide-react';

export default function ComparisonTable() {
  const rows = [
    { name: "Local Code Execution", ecip: "100% Local", cloud: "Cloud Required", ecipGood: true },
    { name: "Open Source License", ecip: "MIT Open Source", cloud: "Proprietary", ecipGood: true },
    { name: "Offline Air-Gapped Usage", ecip: "Supported", cloud: "Impossible", ecipGood: true },
    { name: "Repository-Wide AST Graph", ecip: "Classes, Methods & Links", cloud: "Basic Snippets", ecipGood: true },
    { name: "Hybrid Retrieval (FAISS + BM25)", ecip: "Deterministic Tiering", cloud: "Naive Vector Search", ecipGood: true },
    { name: "Custom Local Model Support", ecip: "Ollama / Qwen / Llama 3", cloud: "Vendor Locked", ecipGood: true },
    { name: "Zero Data Egress Guarantee", ecip: "Zero Network Calls", cloud: "Transmits Source Code", ecipGood: true }
  ];

  return (
    <section className="py-24 bg-[#06080d] border-t border-slate-800/80">
      <div className="max-w-6xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <span>Competitive Matrix</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            ECIP vs Traditional Cloud AI Coding Tools
          </h2>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#090d16] overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-[#0e1424] text-slate-300 font-mono border-b border-slate-800">
                <tr>
                  <th className="p-4 sm:p-5">Capability / Requirement</th>
                  <th className="p-4 sm:p-5 text-cyan-400 font-bold">ECIP Lite (Open Source)</th>
                  <th className="p-4 sm:p-5 text-rose-400">Typical Cloud Assistant</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {rows.map((r, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                    <td className="p-4 sm:p-5 font-medium text-slate-200">{r.name}</td>
                    <td className="p-4 sm:p-5 text-emerald-400 font-semibold flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{r.ecip}</span>
                    </td>
                    <td className="p-4 sm:p-5 text-slate-400 flex items-center gap-2">
                      <X className="w-4 h-4 text-rose-400 shrink-0" />
                      <span>{r.cloud}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </section>
  );
}
