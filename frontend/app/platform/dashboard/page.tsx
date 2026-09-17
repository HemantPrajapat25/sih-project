"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Globe, Building2, ShieldCheck, TrendingUp, AlertTriangle, CheckCircle2,
  Cpu, Users2, Key, Activity, ArrowRight, RefreshCw, Zap, Lock,
} from "lucide-react";

const MOCK_ORGS = [
  { name: "DemoTel Telecom", type: "TELECOM", status: "ACTIVE", numbers: 1480, users: 12, health: 98 },
  { name: "SecureBank Ltd", type: "BANK", status: "ACTIVE", numbers: 0, users: 5, health: 97 },
  { name: "PayFlow Fintech", type: "FINTECH", status: "ACTIVE", numbers: 0, users: 3, health: 94 },
  { name: "ShopKart E-Commerce", type: "ECOMMERCE", status: "ACTIVE", numbers: 0, users: 4, health: 99 },
  { name: "Deloitte Compliance", type: "AUDITOR_ORGANIZATION", status: "ACTIVE", numbers: 0, users: 2, health: 100 },
  { name: "RegAnalytics Bureau", type: "PLATFORM", status: "ACTIVE", numbers: 0, users: 1, health: 100 },
];

const TYPE_BADGE: Record<string, string> = {
  TELECOM: "bg-cyan-950 text-cyan-400 border-cyan-800/60",
  BANK: "bg-amber-950 text-amber-400 border-amber-800/60",
  FINTECH: "bg-amber-950 text-amber-400 border-amber-800/60",
  ECOMMERCE: "bg-orange-950 text-orange-400 border-orange-800/60",
  AUDITOR_ORGANIZATION: "bg-rose-950 text-rose-400 border-rose-800/60",
  PLATFORM: "bg-purple-950 text-purple-400 border-purple-800/60",
};

const KPIS = [
  { label: "Total Organisations", value: "6", sub: "Active on platform", icon: Globe, color: "purple" },
  { label: "Numbers Under Management", value: "1,480", sub: "Across all telecoms", icon: Activity, color: "cyan" },
  { label: "Platform Health", value: "99.8%", sub: "Uptime last 30 days", icon: CheckCircle2, color: "emerald" },
  { label: "Security Alerts", value: "2", sub: "Requires admin review", icon: AlertTriangle, color: "rose" },
];

const COLOR_MAP: Record<string, string> = {
  purple: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  cyan:   "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
  emerald:"text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  rose:   "text-rose-400 bg-rose-500/10 border-rose-500/20",
};

export default function PlatformDashboard() {
  const [refreshing, setRefreshing] = useState(false);
  function refresh() { setRefreshing(true); setTimeout(() => setRefreshing(false), 800); }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-purple-400 px-2 py-0.5 rounded-full bg-purple-950 border border-purple-800/60">
              Super Admin
            </span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            Platform Command Center
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60">
              Live
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            NumberGuard global platform management — organisations, integrations, policies.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button onClick={refresh} className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white transition-colors">
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          </button>
          <Link href="/platform/organizations"
            className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-md shadow-purple-500/20">
            <Building2 className="w-3.5 h-3.5" />
            Manage Organisations
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {KPIS.map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">{label}</span>
              <div className={`p-2 rounded-lg border ${COLOR_MAP[color]}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-[11px] text-slate-500">{sub}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Provision Org", icon: Building2, href: "/platform/organizations", color: "purple" },
          { label: "Manage Users", icon: Users2, href: "/users", color: "cyan" },
          { label: "API Keys", icon: Key, href: "/settings/api-keys", color: "amber" },
          { label: "Integrations", icon: Cpu, href: "/integrations", color: "emerald" },
        ].map(({ label, icon: Icon, href, color }) => (
          <Link key={label} href={href}
            className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 flex flex-col items-center gap-2 text-xs text-slate-400 hover:text-white transition-all group text-center">
            <div className={`p-3 rounded-xl border ${COLOR_MAP[color]} group-hover:scale-110 transition-transform`}>
              <Icon className="w-5 h-5" />
            </div>
            <span className="font-medium">{label}</span>
          </Link>
        ))}
      </div>

      {/* Org Registry Table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div>
            <h2 className="text-sm font-semibold text-white">Organisation Registry</h2>
            <p className="text-xs text-slate-400">All tenant organisations on the NumberGuard platform</p>
          </div>
          <Link href="/platform/organizations" className="text-xs text-purple-400 hover:underline flex items-center gap-1">
            <span>View All</span><ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500">
                {["Organisation", "Type", "Status", "Numbers", "Users", "Health"].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {MOCK_ORGS.map((org) => (
                <tr key={org.name} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-200">{org.name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${TYPE_BADGE[org.type] || TYPE_BADGE.PLATFORM}`}>
                      {org.type.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1.5 text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />{org.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{org.numbers.toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-300">{org.users}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 rounded-full bg-slate-800 max-w-[60px]">
                        <div className="h-full rounded-full bg-emerald-400" style={{ width: `${org.health}%` }} />
                      </div>
                      <span className="text-emerald-400 font-semibold">{org.health}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Security events */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
        <h2 className="text-sm font-semibold text-white mb-3">Platform Security Events</h2>
        <div className="space-y-2">
          {[
            { msg: "API Key rotation due for PayFlow Fintech (expires in 3 days)", sev: "amber" },
            { msg: "Unusual login pattern detected: operator@demotel.demo from new IP", sev: "rose" },
          ].map((e, i) => (
            <div key={i} className={`p-3 rounded-lg border text-xs flex items-center gap-3 ${
              e.sev === "rose" ? "bg-rose-950/40 border-rose-800/60 text-rose-300" : "bg-amber-950/40 border-amber-800/60 text-amber-300"
            }`}>
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {e.msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
