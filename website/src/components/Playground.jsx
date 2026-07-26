import React, { useState } from 'react';
import { Terminal, Code2, Network, FileText, Cpu, CheckCircle } from 'lucide-react';

const PRESETS = [
  {
    title: "🔍 Auth & Token Flow",
    question: "How does authentication & token validation work in this project?",
    answer: `The authentication pipeline is managed across 3 primary components:

1. AuthController.java (L45-L78): Handles POST /api/v1/auth/login. Receives credentials and passes them to UserService.authenticate().
2. JwtTokenService.java (L102-L134): Generates signed JWT payload containing tenant claims, user scopes, and expiration timestamp.
3. JwtSecurityFilter.java (L15-L60): Intercepts all incoming HTTP requests, validates cryptographic signature against local secret key, and injects TenantContext.`,
    ast: `AST Dependency Graph:
  [Class] AuthController
    ├── @RestController
    ├── @Autowired UserService userService
    └── @Autowired JwtTokenService jwtTokenService

  [Class] JwtSecurityFilter extends OncePerRequestFilter
    └── Invocations:
        ├── JwtTokenService.validateToken(String token)
        └── SecurityContextHolder.getContext().setAuthentication(...)`,
    citations: [
      "📄 src/main/java/com/ecip/auth/AuthController.java (Lines 45-78)",
      "📄 src/main/java/com/ecip/auth/JwtTokenService.java (Lines 102-134)",
      "📄 src/main/java/com/ecip/security/JwtSecurityFilter.java (Lines 15-60)"
    ],
    telemetry: `⚡ Retrieval Latency: 14.2 ms\n🧠 Intent Analysis: "qa_explain" (Confidence: 0.98)\n📦 Retrieved Chunks: 4 (2 Hybrid, 2 AST Method)\n🦙 Ollama Model: qwen2.5-coder:7b (Total duration: 840 ms)`
  },
  {
    title: "⚡ Impact Analysis of UserService",
    question: "What classes are impacted if I change UserService method signatures?",
    answer: `Impact Analysis Engine executed downstream dependency graph traversal at depth=3:

Changes to UserService.java affect 7 downstream components:

• Controllers (Direct Callers):
  - AuthController.java (calls UserService.login, UserService.register)
  - UserController.java (calls UserService.getProfile, UserService.updateRole)

• Services & Workers (Indirect Dependencies):
  - AuditLogService.java (subscribes to UserCreatedEvent)
  - NotificationWorker.java (depends on UserDetails payload)`,
    ast: `Graph Traversal Path:
  UserService (Target Class)
    ├── CALLED_BY ➔ AuthController.java (Line 52)
    ├── CALLED_BY ➔ UserController.java (Line 34, 88)
    ├── DEPENDS_ON ➔ UserRepository.java (Field Injection)
    └── EVENT_BUS ➔ AuditLogService.java (Subscriber)`,
    citations: [
      "📄 src/main/java/com/ecip/service/UserService.java (Target)",
      "📄 src/main/java/com/ecip/controller/AuthController.java",
      "📄 src/main/java/com/ecip/controller/UserController.java"
    ],
    telemetry: `⚡ Graph Traversal Latency: 6.8 ms\n🧠 Intent Analysis: "impact_analysis" (Routed to Graph Engine)\n🌐 Graph Nodes Evaluated: 14 nodes, 22 directed edges`
  },
  {
    title: "📦 Database Schema & Models",
    question: "Where are database tables and Flyway SQL migrations defined?",
    answer: `Database tables and schema migrations are configured in 2 layers:

1. Flyway SQL Migration Scripts:
   - V1__init_schema.sql: Defines users, roles, permissions, and foreign key constraints.
   - V2__add_indexes.sql: Contains performance indexes on users.email and tenant_id.

2. JPA Entity Models:
   - UserEntity.java (mapped to users table)
   - RoleEntity.java (mapped to roles table)`,
    ast: `SQL & JPA Metadata Parsing:
  [SQL Table] users
    ├── Column: id (BIGINT, PRIMARY KEY)
    ├── Column: email (VARCHAR, UNIQUE)
    └── Column: tenant_id (VARCHAR, NOT NULL)

  [JPA Entity] UserEntity.java
    ├── @Table(name = "users")
    └── @OneToMany List<RoleEntity> roles`,
    citations: [
      "📄 src/main/resources/db/migration/V1__init_schema.sql",
      "📄 src/main/java/com/ecip/model/UserEntity.java (Lines 1-65)"
    ],
    telemetry: `⚡ Hybrid Search Latency: 11.5 ms\n🧠 Intent Analysis: "schema_lookup"\n📦 Chunks Retrieved: 3 SQL DDL tables, 2 Java Entities`
  }
];

export default function Playground() {
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [activeTab, setActiveTab] = useState('answer');

  const current = PRESETS[selectedPreset];

  return (
    <section id="demo" className="py-24 bg-[#080c14] relative border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <Terminal className="w-3.5 h-3.5" />
            <span>Interactive Simulator</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            See ECIP Reasoning in Action
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            Test how ECIP processes repository questions, traverses AST call graphs, and validates citations.
          </p>
        </div>

        {/* Playground Container */}
        <div className="grid grid-cols-1 lg:grid-cols-12 rounded-2xl bg-[#0a0f1d] border border-cyan-500/30 overflow-hidden shadow-2xl shadow-cyan-500/10">
          
          {/* Preset Queries Sidebar */}
          <div className="lg:col-span-4 bg-[#0d1324] p-6 border-b lg:border-b-0 lg:border-r border-slate-800 space-y-4">
            <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
              Select Preset Scenario
            </div>
            
            {PRESETS.map((p, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedPreset(idx)}
                className={`w-full text-left p-3.5 rounded-xl border text-xs font-medium transition-all cursor-pointer flex items-center justify-between ${
                  selectedPreset === idx
                    ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300 shadow-md'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <span>{p.title}</span>
                {selectedPreset === idx && <CheckCircle className="w-4 h-4 text-cyan-400" />}
              </button>
            ))}
          </div>

          {/* Output Window */}
          <div className="lg:col-span-8 p-6 space-y-4 flex flex-col justify-between">
            <div>
              {/* Question Bar */}
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-cyan-300 flex items-center gap-2 mb-4">
                <span className="text-purple-400 font-bold">Ask ECIP &gt;</span>
                <span className="text-slate-200 font-semibold">{current.question}</span>
              </div>

              {/* Output Tabs */}
              <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-4">
                <button
                  onClick={() => setActiveTab('answer')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    activeTab === 'answer' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  LLM Answer
                </button>
                <button
                  onClick={() => setActiveTab('ast')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    activeTab === 'ast' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  AST & Call Graph
                </button>
                <button
                  onClick={() => setActiveTab('citations')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    activeTab === 'citations' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Citations ({current.citations.length})
                </button>
                <button
                  onClick={() => setActiveTab('telemetry')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    activeTab === 'telemetry' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Telemetry
                </button>
              </div>

              {/* Display Output */}
              <div className="bg-[#05080f] border border-slate-800 rounded-xl p-4 font-mono text-xs min-h-[220px] text-slate-300 leading-relaxed overflow-x-auto">
                {activeTab === 'answer' && (
                  <pre className="white-space-pre-wrap font-sans text-slate-300 text-xs sm:text-sm leading-relaxed">
                    {current.answer}
                  </pre>
                )}

                {activeTab === 'ast' && (
                  <pre className="text-purple-300 text-xs">{current.ast}</pre>
                )}

                {activeTab === 'citations' && (
                  <div className="space-y-2">
                    {current.citations.map((c, i) => (
                      <div key={i} className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-800/40 text-emerald-300 font-mono text-xs">
                        {c}
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'telemetry' && (
                  <pre className="text-amber-300 text-xs">{current.telemetry}</pre>
                )}
              </div>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
}
