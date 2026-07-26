import React, { useState } from 'react';
import { CheckCircle } from 'lucide-react';

const PRESETS = [
  {
    title: "Auth & Token Flow",
    question: "How does authentication & token validation work?",
    answer: `The authentication pipeline spans 3 primary components:

1. AuthController.java (L45-L78): Handles POST /api/v1/auth/login and validates credentials via UserService.
2. JwtTokenService.java (L102-L134): Generates signed JWT payload with tenant claims, user scopes, and expiry timestamp.
3. JwtSecurityFilter.java (L15-L60): Intercepts HTTP requests, validates cryptographic signature locally, and injects TenantContext.`,
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
      { file: "AuthController.java (Lines 45-78)", tier: "FAISS Tier 1", color: "indigo" },
      { file: "JwtTokenService.java (Lines 102-134)", tier: "Class Match", color: "purple" },
      { file: "JwtSecurityFilter.java (Lines 15-60)", tier: "Vector 0.94", color: "emerald" },
    ],
    telemetry: null
  },
  {
    title: "Impact Analysis",
    question: "What breaks if I change UserService method signatures?",
    answer: `Impact Analysis traversed the downstream dependency graph at depth=3:

Changes to UserService.java affect 7 downstream components:

• Direct Controllers:
  - AuthController.java (calls UserService.login, UserService.register)
  - UserController.java (calls UserService.getProfile, UserService.updateRole)

• Indirect Consumers:
  - AuditLogService.java (subscribes to UserCreatedEvent)
  - NotificationWorker.java (depends on UserDetails payload)`,
    ast: `Graph Traversal:
  UserService (Target)
    ├── CALLED_BY ➔ AuthController.java (Line 52)
    ├── CALLED_BY ➔ UserController.java (Line 34, 88)
    ├── DEPENDS_ON ➔ UserRepository.java
    └── EVENT_BUS ➔ AuditLogService.java`,
    citations: [
      { file: "UserService.java (Target)", tier: "Primary", color: "indigo" },
      { file: "AuthController.java", tier: "Depth 1", color: "purple" },
      { file: "UserController.java", tier: "Depth 1", color: "emerald" },
    ],
    telemetry: null
  },
  {
    title: "Database Schema",
    question: "Where are database tables and SQL migrations defined?",
    answer: `Database tables and schema migrations are configured in 2 layers:

1. Flyway SQL Migration Scripts:
   - V1__init_schema.sql: Defines users, roles, permissions with FK constraints.
   - V2__add_indexes.sql: Performance indexes on users.email and tenant_id.

2. JPA Entity Models:
   - UserEntity.java (mapped to users table)
   - RoleEntity.java (mapped to roles table)`,
    ast: `SQL & JPA Metadata:
  [Table] users
    ├── id (BIGINT, PK)
    ├── email (VARCHAR, UNIQUE)
    └── tenant_id (VARCHAR)

  [JPA] UserEntity.java
    ├── @Table(name = "users")
    └── @OneToMany List<RoleEntity> roles`,
    citations: [
      { file: "V1__init_schema.sql", tier: "SQL Migration", color: "indigo" },
      { file: "V2__add_indexes.sql", tier: "SQL Migration", color: "amber" },
      { file: "UserEntity.java (Lines 1-65)", tier: "JPA Entity", color: "emerald" },
    ],
    telemetry: null
  }
];

const colorMap = {
  indigo: "bg-indigo-50 border-indigo-100 text-indigo-700",
  purple: "bg-purple-50 border-purple-100 text-purple-700",
  emerald: "bg-emerald-50 border-emerald-100 text-emerald-700",
  amber: "bg-amber-50 border-amber-100 text-amber-700",
};

export default function Playground() {
  const [selected, setSelected] = useState(0);
  const [tab, setTab] = useState('answer');
  const current = PRESETS[selected];

  return (
    <section id="demo" className="section-light py-24">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        
        <div className="text-center max-w-2xl mx-auto space-y-4 mb-14">
          <div className="section-badge mx-auto w-fit">Interactive Demo</div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            See ECIP reasoning in action
          </h2>
          <p className="text-gray-500 text-base sm:text-lg">
            Test real query scenarios and inspect how ECIP retrieves, reasons, and cites answers.
          </p>
        </div>

        {/* Playground Container */}
        <div className="card-float max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-12">
            
            {/* Preset Sidebar */}
            <div className="md:col-span-4 bg-gray-50 border-b md:border-b-0 md:border-r border-gray-100 p-5 space-y-2">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Select Scenario</div>
              {PRESETS.map((p, i) => (
                <button
                  key={i}
                  onClick={() => { setSelected(i); setTab('answer'); }}
                  className={`w-full text-left p-3.5 rounded-xl text-sm font-medium transition-all cursor-pointer flex items-center justify-between ${
                    selected === i
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <span>{p.title}</span>
                  {selected === i && <CheckCircle className="w-4 h-4 opacity-80" />}
                </button>
              ))}
            </div>

            {/* Output Panel */}
            <div className="md:col-span-8 p-5 space-y-4">
              {/* Query Bar */}
              <div className="bg-indigo-50 border border-indigo-200 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
                <span className="text-indigo-400 font-mono font-bold text-xs shrink-0">Ask ECIP &gt;</span>
                <span className="text-gray-700 font-medium">{current.question}</span>
              </div>

              {/* Tabs */}
              <div className="flex items-center gap-1 border-b border-gray-100 pb-2">
                {[['answer','Answer'],['ast','AST Graph'],['citations','File Citations']].map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setTab(key)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      tab === key
                        ? 'bg-indigo-600 text-white'
                        : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* Content */}
              <div className="border border-gray-100 rounded-xl bg-white p-4 min-h-[200px] overflow-x-auto text-sm shadow-sm">
                {tab === 'answer' && (
                  <pre className="whitespace-pre-wrap text-gray-700 text-sm leading-relaxed font-sans">{current.answer}</pre>
                )}
                {tab === 'ast' && (
                  <pre className="text-indigo-700 text-xs leading-relaxed font-mono">{current.ast}</pre>
                )}
                {tab === 'citations' && (
                  <div className="space-y-2">
                    {current.citations.map((c, i) => (
                      <div key={i} className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${colorMap[c.color]}`}>
                        <span className="font-medium">📄 {c.file}</span>
                        <span className="opacity-70">{c.tier}</span>
                      </div>
                    ))}
                  </div>
                )}
                {tab === 'telemetry' && (
                  <pre className="text-gray-600 text-xs leading-relaxed font-mono">{current.telemetry}</pre>
                )}
              </div>
            </div>

          </div>
        </div>

      </div>
    </section>
  );
}
