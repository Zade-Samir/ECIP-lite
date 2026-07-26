import React from 'react';
import { X } from 'lucide-react';

export default function DownloadModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-3xl max-w-3xl w-full p-8 relative shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto border border-gray-100"
        onClick={e => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-8 h-8 rounded-full bg-gray-100 text-gray-400 hover:text-gray-700 hover:bg-gray-200 transition-all flex items-center justify-center cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        <div>
          <div className="section-badge mb-3 w-fit">RELEASE v1.2.0</div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900">Download ECIP Open Source</h2>
          <p className="text-gray-500 text-sm mt-1">Select your operating system or deployment method.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { emoji: "🍎", os: "macOS", desc: "Apple Silicon & Intel", label: "Source Install" },
            { emoji: "🐧", os: "Linux", desc: "Ubuntu, Debian, Fedora, Arch", label: "Script Install" },
            { emoji: "🪟", os: "Windows", desc: "Windows 11 / WSL2", label: "WSL Setup" },
            { emoji: "🐳", os: "Docker", desc: "Containerized Server", label: "Pull Image" },
          ].map((d, i) => (
            <a
              key={i}
              href="https://github.com/Zade-Samir/ECIP-lite"
              target="_blank"
              rel="noopener noreferrer"
              className="feature-card text-center space-y-3 no-underline block"
            >
              <div className="text-3xl">{d.emoji}</div>
              <div className="font-bold text-gray-900 text-sm">{d.os}</div>
              <div className="text-[11px] text-gray-400">{d.desc}</div>
              <div className="btn-primary justify-center text-xs px-3 py-2 w-full">
                {d.label}
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
