import React, { useState } from 'react';
import { Calculator, Cpu, HardDrive, Clock, Zap } from 'lucide-react';

export default function RepositoryCalculator() {
  const [loc, setLoc] = useState(500000);

  const estimatedChunks = Math.round(loc / 12);
  const initialIndexTimeMins = Math.round((loc / 14200) / 60 * 10) / 10;
  const memoryUsageMB = Math.round(30 + (estimatedChunks * 0.0018));

  return (
    <section className="section-light py-24">
      <div className="max-w-6xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-2xl mx-auto space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">
            <Calculator className="w-3.5 h-3.5" />
            Performance Estimator
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            How ECIP scales for your repository
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            Drag the slider to estimate indexing time and memory footprint for your codebase size.
          </p>
        </div>

        <div className="card-float p-8 sm:p-10 max-w-4xl mx-auto">
          
          {/* Slider */}
          <div className="space-y-4 mb-10">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-gray-700 text-sm">Repository Lines of Code (LOC)</span>
              <span className="font-extrabold text-2xl text-indigo-600 font-mono">{loc.toLocaleString()}</span>
            </div>
            <input
              type="range"
              min="10000"
              max="2000000"
              step="10000"
              value={loc}
              onChange={(e) => setLoc(Number(e.target.value))}
              className="w-full h-2 rounded-full appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-400 font-medium">
              <span>10k — Small project</span>
              <span>500k — Enterprise repo</span>
              <span>2M — Large monorepo</span>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 border-t border-gray-100 pt-8">
            <div className="text-center p-4 rounded-2xl bg-indigo-50 border border-indigo-100">
              <Cpu className="w-5 h-5 text-indigo-500 mx-auto mb-2" />
              <div className="text-2xl font-extrabold text-indigo-700 font-mono">~{estimatedChunks.toLocaleString()}</div>
              <div className="text-xs text-gray-500 mt-1 font-medium">AST Method Chunks</div>
            </div>
            <div className="text-center p-4 rounded-2xl bg-indigo-50 border border-indigo-100">
              <Clock className="w-5 h-5 text-indigo-500 mx-auto mb-2" />
              <div className="text-2xl font-extrabold text-indigo-700 font-mono">~{initialIndexTimeMins} min</div>
              <div className="text-xs text-gray-500 mt-1 font-medium">Initial Index Time</div>
            </div>
            <div className="text-center p-4 rounded-2xl bg-emerald-50 border border-emerald-100">
              <Zap className="w-5 h-5 text-emerald-500 mx-auto mb-2" />
              <div className="text-2xl font-extrabold text-emerald-700 font-mono">&lt; 0.2s</div>
              <div className="text-xs text-gray-500 mt-1 font-medium">Incremental Re-index</div>
            </div>
            <div className="text-center p-4 rounded-2xl bg-indigo-50 border border-indigo-100">
              <HardDrive className="w-5 h-5 text-indigo-500 mx-auto mb-2" />
              <div className="text-2xl font-extrabold text-indigo-700 font-mono">~{memoryUsageMB} MB</div>
              <div className="text-xs text-gray-500 mt-1 font-medium">FAISS + SQLite RAM</div>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
}
