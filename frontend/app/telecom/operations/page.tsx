"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Clock, Hash, BellRing, CheckCircle2, ChevronRight,
  Flame, AlertTriangle, RefreshCw, ListTodo,
} from "lucide-react";

const TODAY_QUEUE = [
  { id: "t-001", masked: "+91 98**** *210", carrier: "Jio", task: "Send provider notification", priority: "HIGH", due: "14:00" },
  { id: "t-002", masked: "+91 70**** *448", carrier: "Airtel", task: "Verify cooling period expiry", priority: "MEDIUM", due: "16:00" },
  { id: "t-003", masked: "+91 81**** *993", carrier: "Vi", task: "Manual risk review required", priority: "CRITICAL", due: "12:30" },
  { id: "t-004", masked: "+91 63**** *112", carrier: "BSNL", task: "Mark as eligible for reallocation", priority: "LOW", due: "17:00" },
  { id: "t-005", masked: "+91 95**** *774", carrier: "Jio", task: "Acknowledge banking remediation", priority: "HIGH", due: "13:15" },
];

const PRIORITY_CLS: Record<string, string> = {
  CRITICAL: "text-rose-400 bg-rose-950/60 border-rose-800/50",
  HIGH:     "text-orange-400 bg-orange-950/60 border-orange-800/50",
  MEDIUM:   "text-amber-400 bg-amber-950/60 border-amber-800/50",
  LOW:      "text-emerald-400 bg-emerald-950/60 border-emerald-800/50",
};

export default function TelecomOperationsPage() {
  const [done, setDone] = useState<Set<string>>(new Set());

  function markDone(id: string) {
    setDone(prev => new Set([...prev, id]));
  }

  const pending = TODAY_QUEUE.filter(t => !done.has(t.id));
  const completed = TODAY_QUEUE.filter(t => done.has(t.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-cyan-400 px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800/60">Telecom Operator</span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ListTodo className="w-5 h-5 text-cyan-400" /> Operations Workspace
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">Your daily task queue — process decommissioning actions and cooling period updates.</p>
        </div>
        <button className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white transition-colors">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Summary chips */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Today's Tasks", value: TODAY_QUEUE.length, icon: ListTodo, color: "cyan" },
          { label: "Pending", value: pending.length, icon: Clock, color: "amber" },
          { label: "Completed", value: completed.length, icon: CheckCircle2, color: "emerald" },
          { label: "Critical", value: TODAY_QUEUE.filter(t => t.priority === "CRITICAL").length, icon: AlertTriangle, color: "rose" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
            <div className={`p-2 rounded-lg border ${
              color === "cyan"    ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-400" :
              color === "amber"   ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
              color === "emerald" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                                    "bg-rose-500/10 border-rose-500/20 text-rose-400"
            }`}><Icon className="w-4 h-4" /></div>
            <div>
              <div className="text-lg font-bold text-white">{value}</div>
              <div className="text-[11px] text-slate-400">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Pending tasks */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800">
          <h2 className="text-sm font-semibold text-white">Pending Tasks</h2>
          <p className="text-xs text-slate-400">Work through these in order of priority. Mark each done when complete.</p>
        </div>
        <div className="divide-y divide-slate-800/60">
          {pending.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-slate-500 text-sm">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              <span>All tasks completed for today! Great work.</span>
            </div>
          ) : (
            pending.map((task) => (
              <div key={task.id} className="px-5 py-4 flex items-center justify-between gap-4 hover:bg-slate-800/20 transition-colors">
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400 flex-shrink-0">
                    <Hash className="w-3.5 h-3.5" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-semibold text-slate-200 text-xs truncate">{task.masked}</div>
                    <div className="text-[11px] text-slate-400 truncate">{task.task}</div>
                    <div className="text-[10px] text-slate-500">{task.carrier} · Due {task.due}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${PRIORITY_CLS[task.priority]}`}>
                    {task.priority}
                  </span>
                  <Link href={`/numbers`} className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white transition-colors">
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                  <button
                    onClick={() => markDone(task.id)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-950 border border-emerald-800/60 text-emerald-400 text-xs font-semibold hover:bg-emerald-900 transition-colors">
                    Done
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Completed */}
      {completed.length > 0 && (
        <div className="rounded-2xl bg-slate-900/40 border border-slate-800/50 overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-800/50">
            <h2 className="text-xs font-semibold text-slate-400">Completed Today ({completed.length})</h2>
          </div>
          <div className="divide-y divide-slate-800/30">
            {completed.map((task) => (
              <div key={task.id} className="px-5 py-3 flex items-center gap-4 opacity-50">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <span className="text-xs text-slate-400 line-through truncate">{task.masked} — {task.task}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick links */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Numbers", href: "/numbers", icon: Hash },
          { label: "Notifications", href: "/notifications", icon: BellRing },
          { label: "Risk View", href: "/risk", icon: Flame },
        ].map(({ label, href, icon: Icon }) => (
          <Link key={label} href={href}
            className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-all">
            <Icon className="w-4 h-4" />{label}
          </Link>
        ))}
      </div>
    </div>
  );
}
