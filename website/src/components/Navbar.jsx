import React, { useState, useEffect } from 'react';
import { Download, BookOpen, Menu, X } from 'lucide-react';

function GithubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

export default function Navbar({ onOpenDownload, onOpenDocs }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handler);
    return () => window.removeEventListener('scroll', handler);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 bg-white transition-all duration-200 ${
        scrolled ? 'border-b border-gray-200 shadow-sm' : 'border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-0 flex items-center justify-between h-16">
        
        {/* Brand Logo */}
        <a href="#" className="flex items-center gap-2.5 flex-shrink-0">
          <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-extrabold text-lg shadow-md shadow-indigo-200">
            ⚡
          </div>
          <span className="font-extrabold text-xl text-gray-900 tracking-tight">ECIP</span>
          <span className="hidden sm:inline-block px-2 py-0.5 rounded-md bg-lime-100 text-lime-700 font-semibold text-xs border border-lime-200">
            Open Source
          </span>
        </a>

        {/* Desktop Navigation Links */}
        <div className="hidden md:flex items-center gap-7 text-sm font-medium text-gray-600">
          <a href="#why-ecip" className="hover:text-indigo-600 transition-colors">Why ECIP</a>
          <a href="#features" className="hover:text-indigo-600 transition-colors">Features</a>
          <a href="#demo" className="hover:text-indigo-600 transition-colors">Playground</a>
          <a href="#architecture" className="hover:text-indigo-600 transition-colors">Architecture</a>
          <button onClick={onOpenDocs} className="hover:text-indigo-600 transition-colors cursor-pointer">Docs</button>
          <a href="#roadmap" className="hover:text-indigo-600 transition-colors">Roadmap</a>
        </div>

        {/* Action Buttons */}
        <div className="hidden md:flex items-center gap-3">
          <a
            href="https://github.com/Zade-Samir/ECIP-lite"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline py-2.5 px-4 text-sm"
          >
            <GithubIcon className="w-4 h-4 text-gray-700" />
            <span>GitHub</span>
          </a>
          <button onClick={onOpenDownload} className="btn-primary py-2.5 px-5 text-sm">
            <Download className="w-4 h-4" />
            <span>Download</span>
          </button>
        </div>

        {/* Mobile Hamburger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 px-4 py-4 space-y-3">
          <a href="#why-ecip" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-gray-700 hover:text-indigo-600">Why ECIP</a>
          <a href="#features" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-gray-700 hover:text-indigo-600">Features</a>
          <a href="#demo" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-gray-700 hover:text-indigo-600">Playground</a>
          <button onClick={() => { onOpenDocs(); setMobileOpen(false); }} className="block py-2 text-sm font-medium text-gray-700 hover:text-indigo-600 text-left w-full">Docs</button>
          <a href="#roadmap" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-gray-700 hover:text-indigo-600">Roadmap</a>
          <div className="pt-2 flex flex-col gap-2">
            <button onClick={onOpenDownload} className="btn-primary justify-center">
              <Download className="w-4 h-4" />Download ECIP
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
