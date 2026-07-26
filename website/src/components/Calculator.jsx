import React, { useState } from 'react';
import { Calculator, Cpu, HardDrive, Clock, Zap } from 'lucide-react';

export default function RepositoryCalculator() {
  const [loc, setLoc] = useState(500000); // Lines of code

  // Calculations based on ECIP performance benchmarks
  const estimatedChunks = Math.round(loc / 12);
  const initialIndexTimeMin = Math.round((loc / 14200) / 60 * 10) / 10;
  const incrementalIndexTimeSec = Math.round((200 / 14200) * 1000) / 1000;
  const memoryUsageMB = Math.round(30 + (estimatedChunks * 0.0018));
  const storageSizeMB = Math.round(5 + (estimatedChunks * 0.006));

  return (
    <section className="py-24 bg-[#070b13] border-t border-slate-800/80 relative">
      <div className="max-w-6xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <Calculator className="w-3.5 h-3.5" />
            <span>Interactive Estimator</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Repository Performance & Memory Estimator
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            Drag the slider to test how ECIP scales for your repository size.
          </p>
        </div>

        <div className="rounded-3xl bg-[#0b101c] border border-cyan-500/30 p-8 sm:p-12 shadow-2xl shadow-cyan-500/10 space-y-8">
          
          {/* Slider Control */}
          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm">
              <span className="font-bold text-slate-300">Repository Lines of Code (LOC)</span>
              <span className="font-mono font-extrabold text-xl text-cyan-400">
                {loc.toLocaleString()} LOC
              </span>
            </div>
            
            <input
              type="range"
              min="10000"
              max="2000000"
              step="10000"
              value={loc}
              onChange={(e) => setLoc(Number(e.target.value))}
              className="w-full h-3 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            
            <div className="flex justify-between text-xs font-mono text-slate-500">
              <span>10k Small Project</span>
              <span>500k Enterprise Repo</span>
              <span>2M+ Monorepo</span>
            </div>
          </div>

          {/* Results Grid (Crypto-Trader Style Ribbon) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-slate-800">
            
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                <Cpu className="w-4 h-4 text-purple-400" />
                <span>EST. CHUNKS</span>
              </div>
              <div className="text-xl font-extrabold text-white font-mono">
                ~{estimatedChunks.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-500">AST Method Nodes</div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span>INITIAL INDEX</span>
              </div>
              <div className="text-xl font-extrabold text-cyan-400 font-mono">
                ~{initialIndexTimeMin} mins
              </div>
              <div className="text-[11px] text-slate-500">First-time scan & embed</div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                <Zap className="w-4 h-4 text-emerald-400" />
                <span>FILE SAVE RE-INDEX</span>
              </div>
              <div className="text-xl font-extrabold text-emerald-400 font-mono">
                &lt; 0.2 sec
              </div>
              <div className="text-[11px] text-slate-500">SHA-256 Incremental pass</div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                <HardDrive className="w-4 h-4 text-amber-400" />
                <span>INDEX RAM USAGE</span>
              </div>
              <div className="text-xl font-extrabold text-amber-400 font-mono">
                ~{memoryUsageMB} MB
              </div>
              <div className="text-[11px] text-slate-500">FAISS Index & SQLite</div>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
}
