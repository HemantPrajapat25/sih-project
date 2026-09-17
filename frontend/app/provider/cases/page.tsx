"use client";

import React, { useState } from "react";
import { FolderOpen, Search, CheckCircle2, Clock, AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";

const CASES = [
  { id: "CASE-2024-001", ref: "REF-A3E89B1F", masked: "+91 98**** *210", category: "Savings Account", status: "OPEN", priority: "HIGH", opened: "2024-09-15", sla: "2h remaining", notes: "Customer has 2 active accounts linked." },
  { id: "CASE-2024-002", ref: "REF-B1A22E9F", masked: "+91 63**** *112", category: "Credit Card", status: "IN_REVIEW", priority: "MEDIUM", opened: "2024-09-14", sla: "8h remaining", notes: "OTP channel delink confirmed. Audit pending." },
  { id: "CASE-2024-003", ref: "REF-C7D21A0E", masked: "+91 70**** *448", category: "Mutual Fund", status: "RESOLVED", priority: "LOW", opened: "2024-09-12", sla: "—", notes: "All associations cleared. Certificate issued." },
  { id: "CASE-2024-004", ref: "REF-D5C83E1A", masked: "+91 77**** *561", category: "Mobile Banking", status: "OPEN", priority: "HIGH", opened: "2024-09-16", sla: "1h remaining", notes: "UPI handle still linked. Urgent." },
  { id: "CASE-2024-005", ref: "REF-E2F91B3C", masked: "+91 88**** *329", category: "Demat Account", status: "RESOLVED", priority: "MEDIUM", opened: "2024-09-10", sla: "—", notes: "Resolved after customer confirmation." },
];

const STATUS_CLS: Record<string, string> = {
  OPEN:       "text-rose-400 bg-rose-950/60 border-rose-800/50",
  IN_REVIEW:  "text-amber-400 bg-amber-950/60 border-amber-800/50",
  RESOLVED:   "text-emerald-400 bg-emerald-950/60 border-emerald-800/50",
};

const P_CLS: Record<string, string> = {
  HIGH:   "text-rose-400",
  MEDIUM: "text-amber-400",
  LOW:    "text-emerald-400",
};

export default function ProviderCasesPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("ALL");
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = CASES.filter(c =>
    (filter === "ALL" || c.status === filter) &&
    (c.id.includes(search) || c.ref.includes(search) || c.category.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-amber-400 px-2 py-0.5 rounded-full bg-amber-950 border border-amber-800/60">Provider</span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-amber-400" /> Unlinking Cases
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">All customer association delink cases for SecureBank Ltd.</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-full bg-rose-950 border border-rose-800/60 text-rose-400">
            {CASES.filter(c => c.status === "OPEN").length} Open
          </span>
          <span className="px-2.5 py-1 rounded-full bg-amber-950 border border-amber-800/60 text-amber-400">
            {CASES.filter(c => c.status === "IN_REVIEW").length} In Review
          </span>
          <span className="px-2.5 py-1 rounded-full bg-emerald-950 border border-emerald-800/60 text-emerald-400">
            {CASES.filter(c => c.status === "RESOLVED").length} Resolved
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search cases…"
            className="pl-9 pr-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500 placeholder-slate-600 w-56"
          />
        </div>
        <div className="flex gap-1.5">
          {["ALL", "OPEN", "IN_REVIEW", "RESOLVED"].map(s => (
            <button key={s} onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filter === s ? "bg-amber-600 text-white" : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
              }`}>{s.replace("_", " ")}</button>
          ))}
        </div>
      </div>

      {/* Cases list */}
      <div className="space-y-2">
        {filtered.map(c => (
          <div key={c.id} className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden">
            <button
              onClick={() => setExpanded(expanded === c.id ? null : c.id)}
              className="w-full px-5 py-4 flex items-center justify-between gap-4 text-left hover:bg-slate-800/20 transition-colors"
            >
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className="text-xs">
                  <div className="font-bold text-slate-200">{c.id}</div>
                  <div className="text-slate-500 font-mono text-[11px]">{c.ref}</div>
                </div>
                <div className="hidden md:block text-xs">
                  <div className="text-slate-300">{c.category}</div>
                  <div className="font-mono text-slate-500 text-[11px]">{c.masked}</div>
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className={`text-[10px] font-semibold ${P_CLS[c.priority]}`}>{c.priority}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${STATUS_CLS[c.status]}`}>{c.status.replace("_", " ")}</span>
                <span className="text-[10px] text-slate-500">{c.sla}</span>
                {expanded === c.id ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
              </div>
            </button>
            {expanded === c.id && (
              <div className="px-5 pb-5 pt-2 border-t border-slate-800 space-y-3">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  {[
                    { label: "Case ID", value: c.id },
                    { label: "Reference Token", value: c.ref },
                    { label: "Category", value: c.category },
                    { label: "Opened", value: c.opened },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <div className="text-slate-500 text-[10px]">{label}</div>
                      <div className="text-slate-200 font-medium mt-0.5">{value}</div>
                    </div>
                  ))}
                </div>
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400">
                  <strong className="text-slate-300">Notes:</strong> {c.notes}
                </div>
                {c.status !== "RESOLVED" && (
                  <div className="flex gap-2">
                    <button className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-colors">
                      Mark In Review
                    </button>
                    <button className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors">
                      Certify Resolved
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
