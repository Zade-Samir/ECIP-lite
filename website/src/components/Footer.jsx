import React from 'react';
import { Download } from 'lucide-react';

function GithubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

export default function Footer({ onOpenDownload, onOpenDocs }) {
  return (
    <footer className="section-dark">
      {/* CTA Banner */}
      <div className="border-b border-white/10">
        <div className="max-w-5xl mx-auto px-4 lg:px-8 py-20 text-center space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Ship better software, faster.
          </h2>
          <p className="text-gray-400 text-base sm:text-lg max-w-xl mx-auto">
            ECIP gives your team deep, repository-wide code intelligence without compromising on privacy or requiring a cloud subscription.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button
              onClick={onOpenDownload}
              className="btn-primary text-base"
            >
              <Download className="w-4 h-4" />
              Download ECIP — Free
            </button>
            <a
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white/10 border border-white/20 text-white font-semibold text-sm hover:bg-white/15 transition-all"
            >
              <GithubIcon className="w-4 h-4" />
              View on GitHub
            </a>
          </div>
        </div>
      </div>

      {/* Links Grid */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          <div className="space-y-4">
            <div className="flex items-center gap-2 font-extrabold text-xl text-white">
              <span className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-lg">⚡</span>
              <span>ECIP</span>
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">
              Enterprise Code Intelligence Platform. 100% offline, privacy-first AI for enterprise codebases.
            </p>
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              MIT Open Source License
            </div>
          </div>

          <div>
            <h4 className="font-bold text-white text-sm mb-4">Product</h4>
            <ul className="space-y-2.5 text-sm text-gray-400">
              <li><a href="#why-ecip" className="hover:text-white transition-colors">Why ECIP</a></li>
              <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
              <li><a href="#demo" className="hover:text-white transition-colors">Interactive Demo</a></li>
              <li><a href="#architecture" className="hover:text-white transition-colors">Architecture</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white text-sm mb-4">Resources</h4>
            <ul className="space-y-2.5 text-sm text-gray-400">
              <li><button onClick={onOpenDocs} className="hover:text-white transition-colors cursor-pointer">Documentation</button></li>
              <li><a href="#quickstart" className="hover:text-white transition-colors">Quick Start</a></li>
              <li><a href="#roadmap" className="hover:text-white transition-colors">Roadmap</a></li>
              <li><a href="#faq" className="hover:text-white transition-colors">FAQ</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white text-sm mb-4">Community</h4>
            <ul className="space-y-2.5 text-sm text-gray-400">
              <li><a href="https://github.com/Zade-Samir/ECIP-lite" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">GitHub Repository</a></li>
              <li><a href="https://github.com/Zade-Samir/ECIP-lite/issues" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">Report a Bug</a></li>
              <li><a href="https://github.com/Zade-Samir/ECIP-lite/blob/main/CONTRIBUTING.md" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">Contributing Guide</a></li>
              <li><a href="https://github.com/Zade-Samir/ECIP-lite/blob/main/LICENSE" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">MIT License</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-16 pt-8 border-t border-white/10 text-center text-xs text-gray-500">
          &copy; 2026 Enterprise Code Intelligence Platform (ECIP). Open Source MIT License.
        </div>
      </div>
    </footer>
  );
}
