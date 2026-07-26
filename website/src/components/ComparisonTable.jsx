import React from 'react';
import { Check, X } from 'lucide-react';

const ROWS = [
  { feature: "Local Code Execution", ecip: "100% Local", cloud: "Cloud Required" },
  { feature: "Open Source License", ecip: "MIT Open Source", cloud: "Proprietary" },
  { feature: "Offline / Air-Gapped Usage", ecip: "Supported", cloud: "Impossible" },
  { feature: "Repository-Wide AST Graph", ecip: "Classes, Methods & Links", cloud: "Basic File Snippets" },
  { feature: "Hybrid Retrieval (FAISS + BM25)", ecip: "Deterministic Tiering", cloud: "Naive Vector Search" },
  { feature: "Custom Local Model Support", ecip: "Ollama / Qwen / Llama 3", cloud: "Vendor Locked" },
  { feature: "Zero Data Egress Guarantee", ecip: "Zero Network Calls", cloud: "Transmits Source Code" },
];

export default function ComparisonTable() {
  return (
    <section className="section-gray py-24">
      <div className="max-w-5xl mx-auto px-4 lg:px-8">

        <div className="text-center max-w-2xl mx-auto space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">Competitive Matrix</div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            ECIP vs traditional cloud AI coding tools
          </h2>
        </div>

        <div className="card-float overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="px-6 py-4 font-semibold text-gray-500 text-xs uppercase tracking-wide">Capability</th>
                <th className="px-6 py-4 font-bold text-indigo-700 text-xs uppercase tracking-wide">ECIP Lite (Open Source)</th>
                <th className="px-6 py-4 font-bold text-red-500 text-xs uppercase tracking-wide">Typical Cloud Assistant</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {ROWS.map((r, i) => (
                <tr key={i} className="hover:bg-gray-50/60 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-800">{r.feature}</td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-2 text-emerald-700 font-semibold">
                      <Check className="w-4 h-4 text-emerald-500 shrink-0" />
                      {r.ecip}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-2 text-gray-500">
                      <X className="w-4 h-4 text-red-400 shrink-0" />
                      {r.cloud}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </section>
  );
}
