import React from 'react';
import { Download, Lock } from 'lucide-react';

function GithubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

export default function Footer({ onOpenDownload, onOpenDocs }) {
  return (
    <footer className="bg-[#04060a] border-t border-slate-800/80 pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-4 lg:px-8 space-y-16">
        
        {/* Call To Action Banner */}
        <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-slate-900 via-[#0a0f1d] to-slate-900 border border-cyan-500/30 text-center max-w-4xl mx-auto space-y-6 shadow-2xl">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
            Your codebase. Your machine. Your intelligence.
          </h2>
          <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto">
            Run AI-powered code intelligence on your repository without sending your source code anywhere.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap pt-2">
            <button
              onClick={onOpenDownload}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-bold text-sm shadow-lg shadow-cyan-500/25 hover:scale-[1.02] transition-all cursor-pointer"
            >
              Download ECIP Open Source
            </button>
            <a
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm hover:bg-slate-700 transition-all"
            >
              <GithubIcon className="w-4 h-4" />
              <span>View on GitHub</span>
            </a>
          </div>
        </div>

        {/* Links Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-xs sm:text-sm">
          <div className="space-y-4">
            <div className="flex items-center gap-2 font-extrabold text-lg text-white">
              <span className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400">⚡</span>
              <span>ECIP.dev</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Enterprise Code Intelligence Platform — 100% offline, privacy-first AI code intelligence engine.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-white mb-3">Product</h4>
            <ul className="space-y-2 text-slate-400">
              <li><a href="#why-ecip" className="hover:text-cyan-400">Why ECIP</a></li>
              <li><a href="#features" className="hover:text-cyan-400">Capabilities</a></li>
              <li><a href="#demo" className="hover:text-cyan-400">Interactive Demo</a></li>
              <li><a href="#architecture" className="hover:text-cyan-400">Architecture</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white mb-3">Resources</h4>
            <ul className="space-y-2 text-slate-400">
              <li><button onClick={onOpenDocs} className="hover:text-cyan-400 cursor-pointer">Documentation</button></li>
              <li><a href="#quickstart" className="hover:text-cyan-400">Quick Start</a></li>
              <li><a href="#roadmap" className="hover:text-cyan-400">Roadmap</a></li>
              <li><a href="#faq" className="hover:text-cyan-400">FAQ</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white mb-3">Community</h4>
            <ul className="space-y-2 text-slate-400">
              <li><a href="https://github.com/Zade-Samir/ECIP-lite" target="_blank" rel="noreferrer" className="hover:text-cyan-400">GitHub Repo</a></li>
              <li><a href="https://github.com/Zade-Samir/ECIP-lite/issues" target="_blank" rel="noreferrer" className="hover:text-cyan-400">Report Bug</a></li>
              <li><a href="https://github.com/Zade-Samir/ECIP-lite/blob/main/CONTRIBUTING.md" target="_blank" rel="noreferrer" className="hover:text-cyan-400">Contributing</a></li>
              <li><a href="https://github.com/Zade-Samir/ECIP-lite/blob/main/LICENSE" target="_blank" rel="noreferrer" className="hover:text-cyan-400">MIT License</a></li>
            </ul>
          </div>
        </div>

        {/* Bottom Copyright */}
        <div className="pt-8 border-t border-slate-800/80 text-center text-xs text-slate-500">
          &copy; 2026 Enterprise Code Intelligence Platform (ECIP). Open Source MIT License.
        </div>

      </div>
    </footer>
  );
}
