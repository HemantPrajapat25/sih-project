"use client";

import React, { useState } from "react";
import {
  TrendingUp, BarChart3, RefreshCw, ShieldCheck,
  Hash, Clock, Building2, ArrowUpRight, ArrowDownRight,
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, CartesianGrid, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from "recharts";

const LIFECYCLE_TREND = [
  { month: "Apr", decommissioned: 120, cooling: 110, reallocated: 85 },
  { month: "May", decommissioned: 145, cooling: 130, reallocated: 98 },
  { month: "Jun", decommissioned: 180, cooling: 160, reallocated: 125 },
  { month: "Jul", decommissioned: 210, cooling: 190, reallocated: 150 },
  { month: "Aug", decommissioned: 260, cooling: 230, reallocated: 185 },
  { month: "Sep", decommissioned: 310, cooling: 260, reallocated: 220 },
];

const SLA_BY_PROVIDER = [
  { name: "HDFC Bank", avg_sla: 14.2, target: 24 },
  { name: "SBI",       avg_sla: 22.1, target: 24 },
  { name: "Paytm",     avg_sla: 8.4,  target: 24 },
  { name: "PhonePe",   avg_sla: 11.3, target: 24 },
  { name: "Amazon",    avg_sla: 18.7, target: 24 },
  { name: "WhatsApp",  avg_sla: 6.2,  target: 24 },
];

const RISK_RADAR = [
  { factor: "Banking Links",  score: 82 },
  { factor: "Cooling Age",    score: 61 },
  { factor: "SLA Overdue",    score: 44 },
  { factor: "Realloc Hold",   score: 73 },
  { factor: "Multi-Provider", score: 58 },
  { factor: "Carrier Age",    score: 37 },
];

const KPIS = [
  { label: "Numbers Tracked", value: "1,480", change: "+12%", up: true,  sub: "vs last quarter" },
  { label: "Avg Cooling Days", value: "74d",   change: "-8%",  up: false, sub: "improving" },
  { label: "SLA Compliance",  value: "91.4%",  change: "+3.2%",up: true,  sub: "cross-partner avg" },
  { label: "Risk Score Avg",  value: "38/100", change: "-5",   up: false, sub: "lower is better" },
];

export default function AnalyticsDashboard() {
  const [refreshing, setRefreshing] = useState(false);
  function refresh() { setRefreshing(true); setTimeout(() => setRefreshing(false), 800); }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800/60">
              Analyst · Read-Only
            </span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            Risk & Lifecycle Analytics
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Cross-carrier risk heatmaps, SLA compliance curves, and lifecycle velocity metrics.
          </p>
        </div>
        <button onClick={refresh} className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white transition-colors">
          <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {KPIS.map(({ label, value, change, up, sub }) => (
          <div key={label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
            <span className="text-xs text-slate-400">{label}</span>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className={`flex items-center gap-1 text-xs font-semibold ${up ? "text-emerald-400" : "text-rose-400"}`}>
              {up ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
              {change} <span className="text-slate-500 font-normal ml-1">{sub}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lifecycle Trend */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <h2 className="text-sm font-semibold text-white mb-1">Number Lifecycle Trend</h2>
          <p className="text-xs text-slate-400 mb-4">Decommission, cooling, and reallocation velocity — last 6 months</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={LIFECYCLE_TREND}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", fontSize: "12px" }} />
                <Legend wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }} />
                <Line type="monotone" dataKey="decommissioned" stroke="#06b6d4" strokeWidth={2} dot={false} name="Decommissioned" />
                <Line type="monotone" dataKey="cooling" stroke="#f59e0b" strokeWidth={2} dot={false} name="In Cooling" />
                <Line type="monotone" dataKey="reallocated" stroke="#10b981" strokeWidth={2} dot={false} name="Reallocated" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Radar */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <h2 className="text-sm font-semibold text-white mb-1">Risk Factor Radar</h2>
          <p className="text-xs text-slate-400 mb-4">Platform-wide weighted risk contributions</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={RISK_RADAR}>
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis dataKey="factor" stroke="#64748b" fontSize={10} />
                <PolarRadiusAxis stroke="#1e293b" fontSize={9} domain={[0, 100]} />
                <Radar name="Risk Score" dataKey="score" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", fontSize: "12px" }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
        <h2 className="text-sm font-semibold text-white mb-1">Partner SLA Compliance</h2>
        <p className="text-xs text-slate-400 mb-4">Average remediation hours per provider vs. 24h SLA target</p>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={SLA_BY_PROVIDER} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" domain={[0, 28]} stroke="#64748b" fontSize={11} />
              <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} width={72} />
              <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", fontSize: "12px" }} />
              <Bar dataKey="avg_sla" name="Avg SLA (hrs)" radius={[0,4,4,0]}
                fill="#06b6d4"
                label={{ position: "right", fontSize: 10, fill: "#94a3b8", formatter: (v: any) => `${v}h` }}
              />
              <Bar dataKey="target" name="Target (24h)" radius={[0,4,4,0]} fill="#1e293b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center gap-4 mt-3 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5"><span className="w-3 h-1.5 rounded bg-cyan-500 inline-block" /> Actual SLA</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-1.5 rounded bg-slate-700 inline-block" /> 24h Target</span>
        </div>
      </div>

      {/* Read-only notice */}
      <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-xs text-emerald-400 flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 flex-shrink-0" />
        <span>Analytics portal is <strong>read-only</strong>. All data is aggregated and privacy-masked — no subscriber identities exposed.</span>
      </div>
    </div>
  );
}
