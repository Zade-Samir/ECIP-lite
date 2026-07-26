import React from 'react';
import { X, Apple, Terminal } from 'lucide-react';

export default function DownloadModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xl flex items-center justify-center p-4">
      <div className="bg-[#0c101b] border border-cyan-500/40 rounded-3xl max-w-3xl w-full p-8 relative shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
        
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-9 h-9 rounded-full bg-slate-800 text-slate-400 hover:text-white hover:bg-rose-500/80 transition-all flex items-center justify-center cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div>
          <div className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider mb-1">RELEASE v1.2.0</div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Download ECIP Open Source</h2>
          <p className="text-slate-400 text-sm mt-1">Select your operating system or deployment package.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-3">
            <div className="text-3xl">🍎</div>
            <div className="font-bold text-white text-sm">macOS</div>
            <div className="text-[11px] text-slate-400">Apple Silicon (M1/M2/M3/M4) & Intel</div>
            <a
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block w-full py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-bold text-xs shadow-md"
            >
              Source Install
            </a>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-3">
            <div className="text-3xl">🐧</div>
            <div className="font-bold text-white text-sm">Linux</div>
            <div className="text-[11px] text-slate-400">Ubuntu, Debian, Fedora, Arch</div>
            <a
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block w-full py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-bold text-xs shadow-md"
            >
              Script Install
            </a>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-3">
            <div className="text-3xl">🪟</div>
            <div className="font-bold text-white text-sm">Windows</div>
            <div className="text-[11px] text-slate-400">Windows 11 / WSL2</div>
            <a
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block w-full py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-bold text-xs shadow-md"
            >
              WSL Setup
            </a>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-3">
            <div className="text-3xl">🐳</div>
            <div className="font-bold text-white text-sm">Docker</div>
            <div className="text-[11px] text-slate-400">Containerized Server</div>
            <a
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block w-full py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-bold text-xs shadow-md"
            >
              Pull Image
            </a>
          </div>

        </div>

      </div>
    </div>
  );
}
