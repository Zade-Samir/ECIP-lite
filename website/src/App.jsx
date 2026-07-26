import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import MetricsTicker from './components/MetricsTicker';
import WhyEcip from './components/WhyEcip';
import Features from './components/Features';
import Playground from './components/Playground';
import Pipeline from './components/Pipeline';
import ComparisonTable from './components/ComparisonTable';
import Quickstart from './components/Quickstart';
import Roadmap from './components/Roadmap';
import Faq from './components/Faq';
import DownloadModal from './components/DownloadModal';
import DocsModal from './components/DocsModal';
import Footer from './components/Footer';

export default function App() {
  const [isDownloadOpen, setIsDownloadOpen] = useState(false);
  const [isDocsOpen, setIsDocsOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#06080d] text-slate-100 selection:bg-cyan-500 selection:text-black">
      {/* Navbar */}
      <Navbar
        onOpenDownload={() => setIsDownloadOpen(true)}
        onOpenDocs={() => setIsDocsOpen(true)}
      />

      {/* Main Sections */}
      <main>
        <Hero
          onOpenDownload={() => setIsDownloadOpen(true)}
          onOpenDocs={() => setIsDocsOpen(true)}
        />
        <MetricsTicker />
        <WhyEcip />
        <Features />
        <Playground />
        <Pipeline />
        <ComparisonTable />
        <Quickstart />
        <Roadmap />
        <Faq />
      </main>

      {/* Footer */}
      <Footer
        onOpenDownload={() => setIsDownloadOpen(true)}
        onOpenDocs={() => setIsDocsOpen(true)}
      />

      {/* Modals */}
      <DownloadModal
        isOpen={isDownloadOpen}
        onClose={() => setIsDownloadOpen(false)}
      />
      
      <DocsModal
        isOpen={isDocsOpen}
        onClose={() => setIsDocsOpen(false)}
      />
    </div>
  );
}
