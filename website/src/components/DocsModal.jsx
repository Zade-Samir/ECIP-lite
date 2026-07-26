import React, { useState } from 'react';
import { X, BookOpen } from 'lucide-react';

const DOCS = {
  intro: {
    title: "Getting Started",
    content: (
      <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
        <p>ECIP (Enterprise Code Intelligence Platform) is an open-source, offline AI assistant running 100% locally on developer workstations and enterprise server clusters.</p>
        <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 space-y-2">
          <div className="font-semibold text-gray-800 text-xs uppercase tracking-wide">Prerequisites:</div>
          <ul className="list-disc list-inside text-gray-600 space-y-1 text-xs">
            <li>Python 3.10+ installed</li>
            <li>Ollama running locally (<code className="bg-gray-200 text-gray-700 px-1 rounded">ollama serve</code>)</li>
            <li>Minimum 8GB RAM (16GB recommended for 7B/14B models)</li>
          </ul>
        </div>
      </div>
    )
  },
  arch: {
    title: "System Architecture",
    content: (
      <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
        <p>ECIP separates code intelligence into two processing layers:</p>
        <div className="space-y-2">
          <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-100">
            <strong className="text-indigo-700">Deterministic AST Layer:</strong>
            <span className="text-gray-600"> Parses class inheritance, method signatures, annotations, and dependency injection to build call graphs.</span>
          </div>
          <div className="p-3 rounded-xl bg-purple-50 border border-purple-100">
            <strong className="text-purple-700">Probabilistic Vector Layer:</strong>
            <span className="text-gray-600"> Uses FAISS and BM25 to find relevant code snippets from natural language queries.</span>
          </div>
        </div>
      </div>
    )
  },
  indexing: {
    title: "Indexing Codebases",
    content: (
      <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
        <p>To index a repository via REST API:</p>
        <pre className="p-4 rounded-xl bg-gray-900 text-gray-200 text-xs overflow-x-auto">{`curl -X POST "http://localhost:8000/api/v1/index" \\
  -H "Content-Type: application/json" \\
  -d '{"project_path": "/path/to/your/project"}'`}</pre>
      </div>
    )
  },
  api: {
    title: "REST API Reference",
    content: (
      <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
        <p>ECIP exposes standard REST endpoints:</p>
        <div className="space-y-2 font-mono text-xs">
          <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-700">POST /api/v1/query — Submit questions &amp; receive streamed answers</div>
          <div className="p-2.5 rounded-lg bg-purple-50 border border-purple-100 text-purple-700">POST /api/v1/index — Trigger background repository indexing</div>
          <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-700">GET /api/v1/workspaces — List active registered projects</div>
        </div>
      </div>
    )
  }
};

export default function DocsModal({ isOpen, onClose }) {
  const [doc, setDoc] = useState('intro');
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-3xl max-w-4xl w-full p-0 relative shadow-2xl max-h-[85vh] overflow-hidden border border-gray-100 flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2 font-bold text-gray-900">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            ECIP Documentation
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-700 flex items-center justify-center cursor-pointer transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-48 shrink-0 bg-gray-50 border-r border-gray-100 p-4 space-y-1">
            {Object.entries(DOCS).map(([key, { title }]) => (
              <button
                key={key}
                onClick={() => setDoc(key)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                  doc === key ? 'bg-indigo-600 text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                {title}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-xl font-extrabold text-gray-900 mb-5">{DOCS[doc].title}</h2>
            {DOCS[doc].content}
          </div>
        </div>
      </div>
    </div>
  );
}
