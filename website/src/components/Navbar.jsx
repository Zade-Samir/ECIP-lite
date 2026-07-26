import React from 'react';
import { Shield, Download, BookOpen, Terminal, Sparkles } from 'lucide-react';

function GithubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

export default function Navbar({ onOpenDownload, onOpenDocs }) {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#06080d]/80 backdrop-blur-xl border-b border-slate-800/80 px-4 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <a href="#" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            ⚡
          </div>
          <div>
            <div className="font-extrabold text-xl tracking-tight text-white flex items-center gap-1.5">
              ECIP <span className="text-cyan-400 font-mono text-sm font-normal">.dev</span>
            </div>
            <div className="text-[10px] text-emerald-400 font-mono uppercase tracking-wider flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              100% Local & Private
            </div>
          </div>
        </a>

        {/* Desktop Navigation Links */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <a href="#why-ecip" className="hover:text-cyan-400 transition-colors">Why ECIP</a>
          <a href="#features" className="hover:text-cyan-400 transition-colors">Features</a>
          <a href="#demo" className="hover:text-cyan-400 transition-colors">Playground</a>
          <a href="#architecture" className="hover:text-cyan-400 transition-colors">Architecture</a>
          <a href="#privacy" className="hover:text-cyan-400 transition-colors">Privacy</a>
          <button onClick={onOpenDocs} className="hover:text-cyan-400 transition-colors cursor-pointer">Docs</button>
          <a href="#roadmap" className="hover:text-cyan-400 transition-colors">Roadmap</a>
          <a href="#faq" className="hover:text-cyan-400 transition-colors">FAQ</a>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/Zade-Samir/ECIP-lite"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700/60 text-slate-200 text-xs font-semibold hover:border-slate-500 transition-all"
          >
            <GithubIcon className="w-4 h-4 text-slate-300" />
            <span>GitHub</span>
            <span className="px-1.5 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400 font-mono">v1.2.0</span>
          </a>

          <button
            onClick={onOpenDownload}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-cyan-500/25 hover:shadow-purple-500/35 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Download</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
