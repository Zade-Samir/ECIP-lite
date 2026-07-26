import React from 'react';
import { ArrowRight, ShieldCheck, CloudOff, Lock } from 'lucide-react';

export default function WhyEcip() {
  return (
    <section id="why-ecip" className="section-light py-24">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">

        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto space-y-4 mb-16">
          <div className="section-badge mx-auto w-fit">
            <Lock className="w-3.5 h-3.5" />
            Data Sovereignty & Privacy
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Your codebase is private.{' '}
            <span className="text-indigo-600">Your AI should be too.</span>
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            Traditional cloud AI coding assistants send your source code to external servers. ECIP runs entirely on your machine.
          </p>
        </div>

        {/* Side-by-Side Comparison Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Cloud Card — Bad */}
          <div className="rounded-2xl border border-red-200 bg-red-50/50 p-8 space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-100 border border-red-200 text-red-600 text-xs font-bold uppercase tracking-wide">
              <CloudOff className="w-3.5 h-3.5" />
              Typical Cloud AI Assistants
            </div>
            <h3 className="text-xl font-bold text-gray-900">Your source code leaves your premises</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              Proprietary algorithms, API credentials, and domain logic are serialized and sent over the internet to external cloud APIs. Your intellectual property is at risk.
            </p>
            {/* Visual Flow */}
            <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
              <span className="px-3 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-700">Local Code</span>
              <ArrowRight className="w-4 h-4 text-red-400 shrink-0" />
              <span className="px-3 py-1.5 rounded-lg bg-red-100 border border-red-200 text-red-600">Public Internet</span>
              <ArrowRight className="w-4 h-4 text-red-400 shrink-0" />
              <span className="px-3 py-1.5 rounded-lg bg-red-100 border border-red-200 text-red-600">Cloud LLM API</span>
            </div>
          </div>

          {/* ECIP Card — Good */}
          <div className="rounded-2xl border border-indigo-200 bg-indigo-50/50 p-8 space-y-5 shadow-sm">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-100 border border-indigo-200 text-indigo-700 text-xs font-bold uppercase tracking-wide">
              <ShieldCheck className="w-3.5 h-3.5" />
              ECIP Local Platform
            </div>
            <h3 className="text-xl font-bold text-gray-900">100% on-premise, air-gapped intelligence</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              Repository parsing, vector embedding, BM25 indexing, AST graph building, and LLM inference run entirely on your hardware. Zero network telemetry.
            </p>
            {/* Visual Flow */}
            <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
              <span className="px-3 py-1.5 rounded-lg bg-indigo-100 border border-indigo-200 text-indigo-700">Local Repo</span>
              <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="px-3 py-1.5 rounded-lg bg-indigo-100 border border-indigo-200 text-indigo-700">FAISS + AST</span>
              <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="px-3 py-1.5 rounded-lg bg-indigo-100 border border-indigo-200 text-indigo-700">Local Ollama</span>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
