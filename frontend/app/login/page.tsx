"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldCheck, Lock, Mail, ArrowRight, KeyRound, Sparkles, CheckCircle2,
  Globe, Building2, Users2, BarChart3, ClipboardList, Cpu,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Role, getDashboardPath } from "@/types";

interface Persona {
  role: Role;
  email: string;
  title: string;
  org: string;
  orgType: string;
  icon: React.ElementType;
  gradient: string;
  badge: string;
  badgeCls: string;
}

const PERSONAS: Persona[] = [
  {
    role: "SUPER_ADMIN",
    email: "superadmin@numberguard.demo",
    title: "Super Admin",
    org: "NumberGuard Platform",
    orgType: "Platform Authority",
    icon: Globe,
    gradient: "from-purple-600/20 to-purple-900/10",
    badge: "PLATFORM",
    badgeCls: "bg-purple-950 text-purple-400 border-purple-800/60",
  },
  {
    role: "TELECOM_ADMIN",
    email: "telecom.admin@demotel.demo",
    title: "Telecom Admin",
    org: "DemoTel Telecom",
    orgType: "Carrier Lifecycle Lead",
    icon: Building2,
    gradient: "from-cyan-600/20 to-cyan-900/10",
    badge: "TELECOM",
    badgeCls: "bg-cyan-950 text-cyan-400 border-cyan-800/60",
  },
  {
    role: "TELECOM_OPERATOR",
    email: "operator@demotel.demo",
    title: "Telecom Operator",
    org: "DemoTel Telecom",
    orgType: "Carrier Operations",
    icon: Cpu,
    gradient: "from-cyan-600/10 to-cyan-900/10",
    badge: "TELECOM",
    badgeCls: "bg-cyan-950 text-cyan-400 border-cyan-800/60",
  },
  {
    role: "SERVICE_PROVIDER_ADMIN",
    email: "bank.admin@securebank.demo",
    title: "Bank Admin",
    org: "SecureBank Ltd",
    orgType: "Partner Organisation Lead",
    icon: Users2,
    gradient: "from-amber-600/20 to-amber-900/10",
    badge: "BANK",
    badgeCls: "bg-amber-950 text-amber-400 border-amber-800/60",
  },
  {
    role: "SERVICE_PROVIDER_OPERATOR",
    email: "bank.operator@securebank.demo",
    title: "Bank Operator",
    org: "SecureBank Ltd",
    orgType: "SecOps Remediation",
    icon: KeyRound,
    gradient: "from-amber-600/10 to-amber-900/10",
    badge: "BANK",
    badgeCls: "bg-amber-950 text-amber-400 border-amber-800/60",
  },
  {
    role: "SERVICE_PROVIDER_ADMIN",
    email: "fintech.admin@payflow.demo",
    title: "Fintech Admin",
    org: "PayFlow Fintech",
    orgType: "Partner Organisation Lead",
    icon: Users2,
    gradient: "from-orange-600/20 to-orange-900/10",
    badge: "FINTECH",
    badgeCls: "bg-orange-950 text-orange-400 border-orange-800/60",
  },
  {
    role: "ANALYST",
    email: "analyst@numberguard.demo",
    title: "Risk Analyst",
    org: "NumberGuard Analytics",
    orgType: "Regulatory Analytics",
    icon: BarChart3,
    gradient: "from-emerald-600/20 to-emerald-900/10",
    badge: "ANALYST",
    badgeCls: "bg-emerald-950 text-emerald-400 border-emerald-800/60",
  },
  {
    role: "AUDITOR",
    email: "auditor@numberguard.demo",
    title: "External Auditor",
    org: "Deloitte Compliance Bureau",
    orgType: "Compliance & Audit",
    icon: ClipboardList,
    gradient: "from-rose-600/20 to-rose-900/10",
    badge: "AUDITOR",
    badgeCls: "bg-rose-950 text-rose-400 border-rose-800/60",
  },
];

const DEMO_EMAIL_MAP: Record<string, Role> = {
  "superadmin@numberguard.demo": "SUPER_ADMIN",
  "telecom.admin@demotel.demo": "TELECOM_ADMIN",
  "operator@demotel.demo": "TELECOM_OPERATOR",
  "bank.admin@securebank.demo": "SERVICE_PROVIDER_ADMIN",
  "bank.operator@securebank.demo": "SERVICE_PROVIDER_OPERATOR",
  "fintech.admin@payflow.demo": "SERVICE_PROVIDER_ADMIN",
  "analyst@numberguard.demo": "ANALYST",
  "auditor@numberguard.demo": "AUDITOR",
};

export default function LoginPage() {
  const router = useRouter();
  const { login, switchDemoRole } = useAuth();
  const [email, setEmail] = useState("telecom.admin@demotel.demo");
  const [password, setPassword] = useState("numberguard2026");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingRole, setLoadingRole] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await login(email, password);
      const role = DEMO_EMAIL_MAP[email] || "TELECOM_ADMIN";
      router.push(getDashboardPath(role));
    } catch (err: any) {
      setError(err.message || "Invalid credentials.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handlePersonaClick(persona: Persona) {
    setLoadingRole(persona.role + persona.email);
    setError(null);
    try {
      await switchDemoRole(persona.role);
      router.push(getDashboardPath(persona.role));
    } catch (err: any) {
      setError(err.message || "Failed to switch role.");
    } finally {
      setLoadingRole(null);
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-[#070a12]">
      <div className="w-full max-w-5xl flex flex-col gap-6">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <span className="font-bold text-2xl text-white tracking-tight">
              Number<span className="text-cyan-400">Guard</span>
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Privacy-preserving B2B telecom number lifecycle platform
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-5">
          {/* Left: Login Form */}
          <div className="md:col-span-2 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-2xl p-6 flex flex-col justify-between backdrop-blur-xl">
            <div>
              <h1 className="text-lg font-bold text-white">Portal Sign In</h1>
              <p className="text-xs text-slate-400 mt-1">
                Enter your corporate credentials to access your role-specific workspace.
              </p>

              {error && (
                <div className="mt-4 p-3 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 text-xs">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="mt-5 space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Corporate Email</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="email" value={email}
                      onChange={(e) => setEmail(e.target.value)} required
                      className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 placeholder-slate-600"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="password" value={password}
                      onChange={(e) => setPassword(e.target.value)} required
                      className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>
                <button
                  type="submit" disabled={isLoading}
                  className="w-full py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer shadow-lg shadow-cyan-500/20 disabled:opacity-50"
                >
                  {isLoading ? "Authenticating…" : "Sign In to Portal"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/80 space-y-2">
              <div className="flex items-center gap-1.5 text-[11px] text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Zero identity exposure — HMAC-SHA256 masking</span>
              </div>
              <p className="text-[10px] text-slate-500">Protected by NumberGuard Privacy-Preserving Enclave.</p>
            </div>
          </div>

          {/* Right: Persona Cards Grid */}
          <div className="md:col-span-3 flex flex-col gap-3">
            <div className="flex items-center gap-2 text-xs text-cyan-400 font-semibold">
              <Sparkles className="w-4 h-4" />
              <span>Sandbox: 1-Click Demo Persona Access</span>
            </div>
            <p className="text-[11px] text-slate-500 -mt-1">
              8 pre-configured personas covering all 7 RBAC roles across 5 organisation types.
            </p>
            <div className="grid grid-cols-2 gap-2.5">
              {PERSONAS.map((p) => {
                const Icon = p.icon;
                const key = p.role + p.email;
                const busy = loadingRole === key;
                return (
                  <button
                    key={key}
                    onClick={() => handlePersonaClick(p)}
                    disabled={busy || !!loadingRole}
                    className={`group text-left p-3 rounded-xl bg-gradient-to-br ${p.gradient} border border-slate-800 hover:border-slate-700 transition-all cursor-pointer disabled:opacity-50 relative overflow-hidden`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className={`p-1.5 rounded-lg bg-slate-900/60 border border-slate-700`}>
                        <Icon className="w-3.5 h-3.5 text-slate-300" />
                      </div>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${p.badgeCls}`}>
                        {p.badge}
                      </span>
                    </div>
                    <div className="text-xs font-bold text-slate-200 group-hover:text-white transition-colors">
                      {p.title}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5 truncate">{p.org}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5 truncate">{p.orgType}</div>
                    {busy && (
                      <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60 rounded-xl">
                        <div className="w-4 h-4 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
              <KeyRound className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
              <span>
                Each persona generates a scoped JWT with role-specific permissions and navigates directly to that role's dedicated portal. Password for all demo accounts: <code className="text-cyan-400">numberguard2026</code>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
