import React from 'react';

const METRICS = [
  { value: "14,200", unit: "LOC/sec", label: "Indexing Speed", color: "text-indigo-600" },
  { value: "< 18", unit: "ms", label: "Retrieval Latency", color: "text-indigo-600" },
  { value: "100%", unit: "Air-Gapped", label: "Privacy Guarantee", color: "text-emerald-600" },
  { value: "99.4%", unit: "Accuracy", label: "AST Symbol Mapping", color: "text-indigo-600" },
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
                <span className="text-base sm:text-lg font-semibold ml-1 text-gray-500">{m.unit}</span>
              </div>
              <div className="mt-1 text-sm text-gray-500 font-medium">{m.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
