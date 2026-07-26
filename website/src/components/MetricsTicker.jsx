import React from 'react';
import { Activity, Zap, Cpu, Database, Shield, GitBranch } from 'lucide-react';

export default function MetricsTicker() {
  const metrics = [
    {
      icon: <Zap className="w-5 h-5 text-cyan-400" />,
      label: "INDEXING SPEED",
      value: "14,200 LOC/sec",
      sub: "SHA-256 Incremental Check"
    },
    {
      icon: <Activity className="w-5 h-5 text-purple-400" />,
      label: "RETRIEVAL LATENCY",
      value: "< 18 ms",
      sub: "FAISS Vector + BM25 Fusion"
    },
    {
      icon: <Shield className="w-5 h-5 text-emerald-400" />,
      label: "PRIVACY RATING",
      value: "100% Air-Gapped",
      sub: "Zero External Egress"
    },
    {
      icon: <GitBranch className="w-5 h-5 text-amber-400" />,
      label: "AST ACCURACY",
      value: "99.4% Symbol Mapping",
      sub: "Caller / Callee Edge Graph"
    }
  ];

  return (
    <section className="border-y border-slate-800/80 bg-[#070b12] py-8">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((m, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-center gap-4 hover:border-slate-700 transition-all"
            >
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/50">
                {m.icon}
              </div>
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">{m.label}</div>
                <div className="text-lg font-extrabold text-white tracking-tight">{m.value}</div>
                <div className="text-[11px] text-slate-400">{m.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
