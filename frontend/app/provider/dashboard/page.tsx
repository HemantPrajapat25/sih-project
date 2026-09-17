"use client";

import React from "react";
import Link from "next/link";
import {
  BellRing, CheckCircle2, Clock, AlertTriangle, TrendingUp,
  ShieldCheck, ArrowRight, FolderOpen, ListTodo,
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";

const SLA_TREND = [
  { week: "W32", sla: 22 }, { week: "W33", sla: 19 }, { week: "W34", sla: 17 },
  { week: "W35", sla: 21 }, { week: "W36", sla: 15 }, { week: "W37", sla: 13 },
];

const RECENT_NOTICES = [
  { ref: "REF-A3E89B1F", status: "PENDING", masked: "+91 98**** *210", received: "2h ago", sla_remaining: "22h" },
  { ref: "REF-C7D21A0E", status: "ACKNOWLEDGED", masked: "+91 70**** *448", received: "5h ago", sla_remaining: "19h" },
  { ref: "REF-F9B34C2D", status: "REMEDIATED", masked: "+91 81**** *993", received: "1d ago", sla_remaining: "—" },
  { ref: "REF-B1A22E9F", status: "PENDING", masked: "+91 63**** *112", received: "3h ago", sla_remaining: "21h" },
];

const STATUS_CLS: Record<string, string> = {
  PENDING:      "text-amber-400 bg-amber-950/60 border-amber-800/50",
  ACKNOWLEDGED: "text-cyan-400 bg-cyan-950/60 border-cyan-800/50",
  REMEDIATED:   "text-emerald-400 bg-emerald-950/60 border-emerald-800/50",
  FAILED:       "text-rose-400 bg-rose-950/60 border-rose-800/50",
};

export default function ProviderDashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-amber-400 px-2 py-0.5 rounded-full bg-amber-950 border border-amber-800/60">Provider Admin</span>
            <span className="text-[10px] text-slate-400">SecureBank Ltd</span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            Provider Command Center
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-950 text-amber-400 border border-amber-800/60">SecureBank</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage decommission notices, customer unlinking SLAs, and remediation certifications.
          </p>
        </div>
        <Link href="/provider/cases"
          className="px-3.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-md shadow-amber-500/20">
          <FolderOpen className="w-3.5 h-3.5" /> View Active Cases
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Notices Received", value: "64", sub: "Across all linked numbers", icon: BellRing, color: "amber" },
          { label: "Pending Unlinking SLA", value: "18", sub: "Require action within 24h", icon: Clock, color: "rose" },
          { label: "Avg Remediation", value: "13.2 hrs", sub: "This week vs 22h baseline", icon: TrendingUp, color: "cyan" },
          { label: "Cleared Associations", value: "46", sub: "Certified & closed this month", icon: CheckCircle2, color: "emerald" },
        ].map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">{label}</span>
              <div className={`p-2 rounded-lg border ${
                color === "amber"   ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                color === "rose"    ? "bg-rose-500/10 border-rose-500/20 text-rose-400" :
                color === "cyan"    ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-400" :
                                      "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              }`}><Icon className="w-4 h-4" /></div>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-[11px] text-slate-500">{sub}</div>
          </div>
        ))}
      </div>

      {/* SLA Trend + Urgent notices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SLA Trend */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <h2 className="text-sm font-semibold text-white mb-1">Average Remediation SLA (hrs)</h2>
          <p className="text-xs text-slate-400 mb-4">Weekly unlinking response time trend</p>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={SLA_TREND}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="week" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} domain={[0, 30]} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", fontSize: "12px" }} />
                <Line type="monotone" dataKey="sla" stroke="#f59e0b" strokeWidth={2} dot={{ fill: "#f59e0b" }} name="Avg SLA (hrs)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pending SLA breaches */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Urgent: SLA at Risk</h2>
            <Link href="/provider/cases" className="text-xs text-amber-400 hover:underline flex items-center gap-1">
              All Cases <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-2">
            {RECENT_NOTICES.filter(n => n.status === "PENDING").map((n) => (
              <div key={n.ref} className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/50 flex items-center justify-between text-xs">
                <div>
                  <div className="font-mono font-semibold text-amber-300">{n.ref}</div>
                  <div className="text-[11px] text-slate-400">{n.masked} · {n.received}</div>
                </div>
                <div className="text-right">
                  <div className="text-amber-400 font-semibold">{n.sla_remaining}</div>
                  <div className="text-[10px] text-slate-500">remaining</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent notices table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div>
            <h2 className="text-sm font-semibold text-white">Recent Decommission Notices</h2>
            <p className="text-xs text-slate-400">Masked references only — no subscriber identity exposed</p>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" /> Privacy Protected
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500">
                {["Reference Token", "Masked Number", "Status", "Received", "SLA Remaining", ""].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {RECENT_NOTICES.map(n => (
                <tr key={n.ref} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-slate-300">{n.ref}</td>
                  <td className="px-4 py-3 font-mono text-slate-400">{n.masked}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${STATUS_CLS[n.status]}`}>{n.status}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{n.received}</td>
                  <td className="px-4 py-3 text-slate-300">{n.sla_remaining}</td>
                  <td className="px-4 py-3">
                    {n.status === "PENDING" && (
                      <button className="px-2.5 py-1 rounded-lg bg-amber-950 border border-amber-800/60 text-amber-400 text-[10px] font-semibold hover:bg-amber-900 transition-colors">
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
