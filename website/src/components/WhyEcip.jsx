import React from 'react';
import { ShieldAlert, ShieldCheck, ArrowRight, Lock, Server, CloudOff } from 'lucide-react';

export default function WhyEcip() {
  return (
    <section id="why-ecip" className="py-24 bg-[#06080d] relative">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            <Lock className="w-3.5 h-3.5" />
            <span>Data Sovereignty & Privacy</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Your codebase is private.{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Your AI should be too.
            </span>
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            Compare traditional cloud-hosted AI coding assistants against ECIP's local-first architecture.
          </p>
        </div>

        {/* Side by Side Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Cloud Card */}
          <div className="rounded-2xl bg-rose-950/10 border border-rose-500/20 p-8 relative overflow-hidden space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-bold uppercase tracking-wider">
              <CloudOff className="w-4 h-4" />
              <span>Typical Cloud AI Assistant</span>
            </div>

            <h3 className="text-2xl font-bold text-white">Source Code Leaves Your Premises</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Proprietary algorithms, database passwords, and domain logic are serialized and sent over the internet to cloud APIs. Enterprise IP is vulnerable to cloud vendor retention policies.
            </p>

            {/* Visual Flow Diagram */}
            <div className="p-4 rounded-xl bg-[#080c14] border border-slate-800 font-mono text-xs text-slate-300 flex items-center justify-between gap-2 overflow-x-auto">
              <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300">Local Code</span>
              <ArrowRight className="w-4 h-4 text-rose-500 shrink-0" />
              <span className="px-2.5 py-1 rounded bg-rose-950/80 border border-rose-500/40 text-rose-300 shrink-0">Public Internet</span>
              <ArrowRight className="w-4 h-4 text-rose-500 shrink-0" />
              <span className="px-2.5 py-1 rounded bg-rose-950/80 border border-rose-500/40 text-rose-300 shrink-0">Cloud LLM</span>
            </div>
          </div>

          {/* ECIP Card */}
          <div className="rounded-2xl bg-emerald-950/10 border border-emerald-500/30 p-8 relative overflow-hidden space-y-6 shadow-xl shadow-emerald-500/5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-xs font-bold uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4" />
              <span>ECIP Local Platform</span>
            </div>

            <h3 className="text-2xl font-bold text-white">100% On-Premise Air-Gapped Intelligence</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Repository parsing, vector embeddings, BM25 indexing, AST graph building, and LLM inference run strictly on your hardware. Zero network telemetry.
            </p>

            {/* Visual Flow Diagram */}
            <div className="p-4 rounded-xl bg-[#080c14] border border-emerald-500/40 font-mono text-xs text-emerald-300 flex items-center justify-between gap-2 overflow-x-auto">
              <span className="px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 shrink-0">Local Repo</span>
              <ArrowRight className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 shrink-0">Local FAISS + AST</span>
              <ArrowRight className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 shrink-0">Local Ollama LLM</span>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
