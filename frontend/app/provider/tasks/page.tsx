"use client";

import React, { useState } from "react";
import { CheckCircle2, Clock, AlertTriangle, MessageSquare, ChevronDown } from "lucide-react";

const TASKS = [
  { id: "c-001", ref: "REF-A3E89B1F", masked: "+91 98**** *210", action: "Unlink savings account notifications", priority: "HIGH", due: "2h", status: "ASSIGNED" },
  { id: "c-002", ref: "REF-B1A22E9F", masked: "+91 63**** *112", action: "Verify mobile banking OTP channel delink", priority: "HIGH", due: "4h", status: "ASSIGNED" },
  { id: "c-003", ref: "REF-D5C83E1A", masked: "+91 77**** *561", action: "Audit credit card SMS alert association", priority: "MEDIUM", due: "8h", status: "IN_PROGRESS" },
  { id: "c-004", ref: "REF-E2F91B3C", masked: "+91 88**** *329", action: "Certify mutual fund account unlink", priority: "LOW", due: "24h", status: "ASSIGNED" },
];

const P_CLS: Record<string, string> = {
  HIGH:   "text-rose-400 bg-rose-950/60 border-rose-800/50",
  MEDIUM: "text-amber-400 bg-amber-950/60 border-amber-800/50",
  LOW:    "text-emerald-400 bg-emerald-950/60 border-emerald-800/50",
};

const S_CLS: Record<string, string> = {
  ASSIGNED:    "text-slate-400 bg-slate-800 border-slate-700",
  IN_PROGRESS: "text-cyan-400 bg-cyan-950/60 border-cyan-800/50",
  DONE:        "text-emerald-400 bg-emerald-950/60 border-emerald-800/50",
};

export default function ProviderTasksPage() {
  const [statuses, setStatuses] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [openNote, setOpenNote] = useState<string | null>(null);

  function advance(id: string) {
    setStatuses(prev => {
      const cur = prev[id] || TASKS.find(t => t.id === id)?.status || "ASSIGNED";
      const next = cur === "ASSIGNED" ? "IN_PROGRESS" : cur === "IN_PROGRESS" ? "DONE" : "DONE";
      return { ...prev, [id]: next };
    });
  }

  const getStatus = (task: typeof TASKS[0]) => statuses[task.id] || task.status;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-amber-400 px-2 py-0.5 rounded-full bg-amber-950 border border-amber-800/60">Operator</span>
            <span className="text-[10px] text-slate-400">SecureBank Ltd</span>
          </div>
          <h1 className="text-xl font-bold text-white">My Task Queue</h1>
          <p className="text-xs text-slate-400 mt-0.5">Assigned unlinking cases — acknowledge, action, and certify each remediation.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          {TASKS.filter(t => getStatus(t) !== "DONE").length} tasks remaining
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Assigned", count: TASKS.filter(t => getStatus(t) === "ASSIGNED").length, color: "slate" },
          { label: "In Progress", count: TASKS.filter(t => getStatus(t) === "IN_PROGRESS").length, color: "cyan" },
          { label: "Completed", count: TASKS.filter(t => getStatus(t) === "DONE").length, color: "emerald" },
        ].map(({ label, count, color }) => (
          <div key={label} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <div className={`text-2xl font-bold ${color === "emerald" ? "text-emerald-400" : color === "cyan" ? "text-cyan-400" : "text-white"}`}>{count}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Task cards */}
      <div className="space-y-3">
        {TASKS.map((task) => {
          const status = getStatus(task);
          const note = notes[task.id] || "";
          return (
            <div key={task.id} className={`rounded-2xl border transition-all ${
              status === "DONE" ? "bg-slate-900/30 border-slate-800/40 opacity-60" : "bg-slate-900/70 border-slate-800"
            }`}>
              <div className="p-4 flex flex-col md:flex-row md:items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="font-mono text-[11px] text-slate-400">{task.ref}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${P_CLS[task.priority]}`}>{task.priority}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${S_CLS[status]}`}>{status.replace("_", " ")}</span>
                  </div>
                  <div className="font-semibold text-sm text-slate-200">{task.action}</div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    <span className="font-mono">{task.masked}</span> · Due in {task.due}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => setOpenNote(openNote === task.id ? null : task.id)}
                    className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-colors"
                    title="Add case note"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                  </button>
                  {status !== "DONE" && (
                    <button
                      onClick={() => advance(task.id)}
                      className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-colors flex items-center gap-1.5"
                    >
                      {status === "ASSIGNED" ? "Start Task" : "Certify Done"}
                    </button>
                  )}
                  {status === "DONE" && (
                    <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-semibold">
                      <CheckCircle2 className="w-4 h-4" /> Certified
                    </div>
                  )}
                </div>
              </div>
              {openNote === task.id && (
                <div className="px-4 pb-4 border-t border-slate-800 pt-3">
                  <textarea
                    rows={2}
                    value={note}
                    onChange={e => setNotes(prev => ({ ...prev, [task.id]: e.target.value }))}
                    placeholder="Add a case note (e.g. 'Customer confirmed delink via secure channel at 14:30')…"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500 placeholder-slate-600 resize-none"
                  />
                  <button
                    onClick={() => setOpenNote(null)}
                    className="mt-2 px-3 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700 transition-colors"
                  >Save Note</button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
