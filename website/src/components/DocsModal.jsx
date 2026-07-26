import React, { useState } from 'react';
import { X, BookOpen, Terminal, Code, Layers, FileCode } from 'lucide-react';

const DOC_PAGES = {
  intro: {
    title: "1. Getting Started with ECIP",
    content: (
      <div className="space-y-4 text-slate-300 text-xs sm:text-sm leading-relaxed">
        <p>ECIP (Enterprise Code Intelligence Platform) is an open-source, offline AI assistant designed to run 100% locally on developer workstations and enterprise server clusters.</p>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="font-bold text-white text-xs">System Prerequisites:</div>
          <ul className="list-disc list-inside text-slate-400 space-y-1 text-xs">
            <li>Python 3.10+ installed</li>
            <li>Ollama running locally (<code className="text-cyan-400">ollama serve</code>)</li>
            <li>Minimum 8GB RAM (16GB recommended for 7B/14B models)</li>
          </ul>
        </div>
      </div>
    )
  },
  arch: {
    title: "2. System Architecture",
    content: (
      <div className="space-y-4 text-slate-300 text-xs sm:text-sm leading-relaxed">
        <p>ECIP separates code intelligence into two primary processing layers:</p>
        <ul className="space-y-2">
          <li className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <strong className="text-purple-400">Deterministic AST Layer:</strong> Parses class inheritance, method signatures, annotations, and dependency injection to build call graphs.
          </li>
          <li className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <strong className="text-cyan-400">Probabilistic Vector Layer:</strong> Uses FAISS and BM25 to find relevant code snippets based on natural language queries.
          </li>
        </ul>
      </div>
    )
  },
  indexing: {
    title: "3. Indexing Codebases",
    content: (
      <div className="space-y-4 text-slate-300 text-xs sm:text-sm leading-relaxed">
        <p>To index a repository via REST API or CLI:</p>
        <pre className="p-4 rounded-xl bg-[#04060a] border border-slate-800 font-mono text-xs text-cyan-300 overflow-x-auto">
{`curl -X POST "http://localhost:8000/api/v1/index" \\
  -H "Content-Type: application/json" \\
  -d '{"project_path": "/path/to/your/project"}'`}
        </pre>
      </div>
    )
  },
  api: {
    title: "4. REST API Reference",
    content: (
      <div className="space-y-3 text-slate-300 text-xs sm:text-sm leading-relaxed">
        <p>ECIP exposes standard REST endpoints:</p>
        <ul className="space-y-2 font-mono text-xs">
          <li className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-cyan-300">
            POST /api/v1/query — Submit questions & receive streamed answers
          </li>
          <li className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-purple-300">
            POST /api/v1/index — Trigger background repository indexing
          </li>
          <li className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-emerald-300">
            GET /api/v1/workspaces — List active registered projects
          </li>
        </ul>
      </div>
    )
  }
};

export default function DocsModal({ isOpen, onClose }) {
  const [docKey, setDocKey] = useState('intro');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xl flex items-center justify-center p-4">
      <div className="bg-[#0c101b] border border-cyan-500/40 rounded-3xl max-w-4xl w-full p-8 relative shadow-2xl space-y-6 max-h-[85vh] overflow-y-auto">
        
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-9 h-9 rounded-full bg-slate-800 text-slate-400 hover:text-white hover:bg-rose-500/80 transition-all flex items-center justify-center cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          
          {/* Sidebar */}
          <div className="md:col-span-4 space-y-2 border-b md:border-b-0 md:border-r border-slate-800 pb-4 md:pb-0 md:pr-4">
            <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              <span>ECIP Docs</span>
            </div>

            <button
              onClick={() => setDocKey('intro')}
              className={`w-full text-left p-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                docKey === 'intro' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              1. Getting Started
            </button>
            <button
              onClick={() => setDocKey('arch')}
              className={`w-full text-left p-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                docKey === 'arch' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              2. Architecture
            </button>
            <button
              onClick={() => setDocKey('indexing')}
              className={`w-full text-left p-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                docKey === 'indexing' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              3. Indexing Codebases
            </button>
            <button
              onClick={() => setDocKey('api')}
              className={`w-full text-left p-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                docKey === 'api' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              4. REST API Reference
            </button>
          </div>

          {/* Doc Content Area */}
          <div className="md:col-span-8 space-y-4">
            <h2 className="text-xl font-bold text-white">{DOC_PAGES[docKey].title}</h2>
            {DOC_PAGES[docKey].content}
          </div>

        </div>

      </div>
    </div>
  );
}
