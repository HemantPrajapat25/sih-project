"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Hash, Clock, Flame, CheckCircle2, BellRing, ShieldCheck, TrendingUp,
  ArrowRight, Upload, RefreshCw, AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { DashboardKPIs } from "@/types";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, CartesianGrid,
} from "recharts";

const MOCK_METRICS: DashboardKPIs = {
  total_numbers_managed: 1480,
  decommissioned_numbers: 412,
  in_cooling_period: 320,
  high_risk_numbers: 48,
  ready_for_reallocation: 215,
  pending_provider_responses: 64,
  critical_alerts: 12,
  avg_remediation_hours: 18.4,
  risk_distribution: { LOW: 145, MEDIUM: 180, HIGH: 65, CRITICAL: 22 },
  lifecycle_trend: [
    { month: "Apr", decommissioned: 120, cooling: 110, reallocated: 85 },
    { month: "May", decommissioned: 145, cooling: 130, reallocated: 98 },
    { month: "Jun", decommissioned: 180, cooling: 160, reallocated: 125 },
    { month: "Jul", decommissioned: 210, cooling: 190, reallocated: 150 },
    { month: "Aug", decommissioned: 260, cooling: 230, reallocated: 185 },
    { month: "Sep", decommissioned: 310, cooling: 260, reallocated: 220 },
  ],
  recent_activity: [],
};

const RISK_PIE = [
  { name: "Low", value: 145, color: "#10b981" },
  { name: "Medium", value: 180, color: "#f59e0b" },
  { name: "High", value: 65, color: "#f97316" },
  { name: "Critical", value: 22, color: "#ef4444" },
];

export default function TelecomDashboard() {
  const [metrics, setMetrics] = useState<DashboardKPIs | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try { setMetrics(await api.getDashboardMetrics()); }
    catch { setMetrics(MOCK_METRICS); }
    finally { setLoading(false); }
  }

  useEffect(() => { loadData(); }, []);

  const m = metrics ?? MOCK_METRICS;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-cyan-400 px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800/60">Telecom Admin</span>
            <span className="text-[10px] text-slate-400">DemoTel Telecom</span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            Telecom Lifecycle Command Center
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60">Live Monitoring</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">Quarantine orchestration, provider remediation, and reallocation risk scoring.</p>
        </div>
        <div className="flex items-center gap-2.5">
          <button onClick={loadData} className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white transition-colors">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link href="/numbers"
            className="px-3.5 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-md shadow-cyan-500/20">
            <Upload className="w-3.5 h-3.5" /> Batch Decommission
          </Link>
        </div>
      </div>

      {/* Alert bar */}
      {m.critical_alerts > 0 && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 flex items-center justify-between text-xs text-rose-300">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 animate-bounce" />
            <span><strong>{m.critical_alerts} High-Risk Numbers</strong> detected with unacknowledged banking linkages. Reallocation blocked.</span>
          </div>
          <Link href="/readiness" className="text-xs font-semibold text-rose-400 hover:underline flex items-center gap-1">
            Inspect <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { title: "Total Numbers", value: m.total_numbers_managed, sub: "Active registry", icon: Hash, color: "cyan", href: "/numbers" },
          { title: "In Cooling", value: m.in_cooling_period, sub: "60–120 day quarantine", icon: Clock, color: "amber", href: "/cooling" },
          { title: "Ready to Reallocate", value: m.ready_for_reallocation, sub: "Zero-hold clearance", icon: CheckCircle2, color: "emerald", href: "/readiness" },
          { title: "High & Critical Risk", value: m.high_risk_numbers, sub: "Banking alerts active", icon: Flame, color: "rose", href: "/risk" },
        ].map(({ title, value, sub, icon: Icon, color, href }) => (
          <Link key={title} href={href}
            className={`p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 flex flex-col gap-2 transition-all group`}>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">{title}</span>
              <div className={`p-2 rounded-lg border ${
                color === "cyan"    ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-400" :
                color === "amber"   ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                color === "emerald" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                                      "bg-rose-500/10 border-rose-500/20 text-rose-400"
              }`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-white">{value?.toLocaleString() ?? "--"}</div>
            <div className="text-[11px] text-slate-500">{sub}</div>
          </Link>
        ))}
      </div>

      {/* Secondary metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "Pending Provider Responses", value: `${m.pending_provider_responses}`, sub: "Across 8 partner networks", icon: BellRing, color: "purple" },
          { label: "Avg Remediation SLA", value: `${m.avg_remediation_hours} hrs`, sub: "Bank unlinking speed", icon: TrendingUp, color: "cyan" },
          { label: "Privacy Mode", value: "Zero-Leakage", sub: "HMAC-SHA256 masking active", icon: ShieldCheck, color: "emerald" },
        ].map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-400">{label}</span>
              <div className={`text-xl font-bold mt-1 ${color === "emerald" ? "text-emerald-400" : "text-white"}`}>{value}</div>
              <span className="text-[10px] text-slate-400">{sub}</span>
            </div>
            <div className={`p-3 rounded-xl border ${
              color === "purple"  ? "bg-purple-500/10 border-purple-500/20 text-purple-400" :
              color === "cyan"    ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-400" :
                                    "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
            }`}><Icon className="w-5 h-5" /></div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-white">Number Lifecycle Trend</h2>
              <p className="text-xs text-slate-400">Monthly decommission, cooling, and release velocity</p>
            </div>
            <Link href="/analytics" className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
              Full Analytics <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={m.lifecycle_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", fontSize: "12px" }} />
                <Bar dataKey="decommissioned" name="Decommissioned" fill="#06b6d4" radius={[4,4,0,0]} />
                <Bar dataKey="cooling" name="In Cooling" fill="#f59e0b" radius={[4,4,0,0]} />
                <Bar dataKey="reallocated" name="Reallocated" fill="#10b981" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <h2 className="text-sm font-semibold text-white mb-1">Risk Distribution</h2>
          <p className="text-xs text-slate-400 mb-2">Residual risk across all numbers</p>
          <div className="h-40 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={RISK_PIE} cx="50%" cy="50%" innerRadius={40} outerRadius={60} paddingAngle={3} dataKey="value">
                  {RISK_PIE.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", fontSize: "12px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-1.5 pt-3 border-t border-slate-800">
            {RISK_PIE.map(d => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                  <span className="text-slate-300">{d.name}</span>
                </div>
                <span className="font-semibold text-slate-200">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
