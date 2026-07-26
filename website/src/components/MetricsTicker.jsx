import React from 'react';

const METRICS = [
  { value: "14,200", unit: "files/min", label: "Indexing Throughput", sub: "On a standard 8-core machine", color: "text-indigo-600" },
  { value: "< 18", unit: "ms", label: "Query Response Time", sub: "Hybrid FAISS + BM25 retrieval", color: "text-indigo-600" },
  { value: "100%", unit: "Local", label: "Privacy Guarantee", sub: "No data leaves your machine", color: "text-emerald-600" },
  { value: "Java", unit: "+ more", label: "Language Support", sub: "Python, TS, Go, Rust in v2.0", color: "text-indigo-600" },
];

export default function MetricsTicker() {
  return (
    <section className="section-gray border-y border-gray-200 py-12">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 divide-y lg:divide-y-0 lg:divide-x divide-gray-200">
          {METRICS.map((m, idx) => (
            <div key={idx} className={`${idx > 0 ? 'pt-8 lg:pt-0 lg:pl-8' : ''} text-center lg:text-left`}>
              <div className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${m.color}`}>
                {m.value}
                <span className="text-base sm:text-lg font-semibold ml-1 text-gray-400">{m.unit}</span>
              </div>
              <div className="mt-1 text-sm text-gray-700 font-semibold">{m.label}</div>
              <div className="mt-0.5 text-xs text-gray-400">{m.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
