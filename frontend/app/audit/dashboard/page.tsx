"use client";

import React, { useState } from "react";
import {
  ClipboardList, Search, Filter, ShieldCheck, AlertOctagon,
  CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronRight,
} from "lucide-react";

const AUDIT_EVENTS = [
  { id: "AUD-0091", actor: "telecom.admin@demotel.demo", role: "TELECOM_ADMIN", action: "NUMBER_DECOMMISSIONED", entity: "MobileNumber", entity_id: "num-0042", result: "SUCCESS", ip: "10.0.1.44", correlation: "COR-9A3E21F0", ts: "2024-09-17T08:14:22Z", details: "Batch decommission triggered via CSV upload" },
  { id: "AUD-0090", actor: "operator@demotel.demo",       role: "TELECOM_OPERATOR", action: "NOTIFICATION_SENT",   entity: "ProviderNotification", entity_id: "ntf-0133", result: "SUCCESS", ip: "10.0.1.51", correlation: "COR-3B9D50A1", ts: "2024-09-17T07:55:10Z", details: "Sent to SecureBank via webhook" },
  { id: "AUD-0089", actor: "bank.admin@securebank.demo",  role: "SERVICE_PROVIDER_ADMIN", action: "NOTIFICATION_ACKNOWLEDGED", entity: "ProviderNotification", entity_id: "ntf-0129", result: "SUCCESS", ip: "203.90.12.5", correlation: "COR-7C1E8F2B", ts: "2024-09-17T06:42:55Z", details: "Bank acknowledged via portal" },
  { id: "AUD-0088", actor: "operator@demotel.demo",       role: "TELECOM_OPERATOR", action: "RISK_SCORE_OVERRIDE",  entity: "DecommissionedNumber", entity_id: "dcm-0077", result: "SUCCESS", ip: "10.0.1.51", correlation: "COR-2A4F6E9D", ts: "2024-09-16T23:11:03Z", details: "Manual override: score raised to CRITICAL after banking linkage confirmed" },
  { id: "AUD-0087", actor: "superadmin@numberguard.demo", role: "SUPER_ADMIN",    action: "COOLING_RULE_MODIFIED", entity: "CoolingRule", entity_id: "rul-0003", result: "SUCCESS", ip: "172.16.0.1", correlation: "COR-5B8A1D3C", ts: "2024-09-16T18:30:00Z", details: "Extended banking-associated cooling from 90d to 120d" },
  { id: "AUD-0086", actor: "analyst@numberguard.demo",    role: "ANALYST",       action: "REPORT_GENERATED",      entity: "Report", entity_id: "rpt-0012", result: "SUCCESS", ip: "10.0.2.88", correlation: "COR-6C9B2E4A", ts: "2024-09-16T15:00:00Z", details: "Monthly risk distribution report generated" },
  { id: "AUD-0085", actor: "bank.operator@securebank.demo", role: "SERVICE_PROVIDER_OPERATOR", action: "CASE_CERTIFIED", entity: "Case", entity_id: "CASE-2024-003", result: "SUCCESS", ip: "203.90.12.6", correlation: "COR-1D4F7A8B", ts: "2024-09-16T11:22:44Z", details: "Remediation certified — mutual fund association cleared" },
  { id: "AUD-0084", actor: "operator@demotel.demo",       role: "TELECOM_OPERATOR", action: "NUMBER_REALLOCATED",  entity: "MobileNumber", entity_id: "num-0031", result: "FAILED", ip: "10.0.1.51", correlation: "COR-8E2C9B5D", ts: "2024-09-16T09:10:01Z", details: "Reallocation blocked — pending HIGH risk provider ACK" },
];

const RESULT_CLS: Record<string, { cls: string; icon: React.ElementType }> = {
  SUCCESS: { cls: "text-emerald-400 bg-emerald-950/60 border-emerald-800/50", icon: CheckCircle2 },
  FAILED:  { cls: "text-rose-400 bg-rose-950/60 border-rose-800/50",         icon: XCircle },
  WARNING: { cls: "text-amber-400 bg-amber-950/60 border-amber-800/50",      icon: AlertTriangle },
};

const ROLE_CLS: Record<string, string> = {
  SUPER_ADMIN:               "text-purple-400",
  TELECOM_ADMIN:             "text-cyan-400",
  TELECOM_OPERATOR:          "text-cyan-300",
  SERVICE_PROVIDER_ADMIN:    "text-amber-400",
  SERVICE_PROVIDER_OPERATOR: "text-amber-300",
  ANALYST:                   "text-emerald-400",
  AUDITOR:                   "text-rose-400",
};

const ACTION_HIGHLIGHT: Record<string, string> = {
  NUMBER_DECOMMISSIONED:      "text-cyan-300",
  RISK_SCORE_OVERRIDE:        "text-rose-300",
  COOLING_RULE_MODIFIED:      "text-amber-300",
  NUMBER_REALLOCATED:         "text-emerald-300",
  NOTIFICATION_SENT:          "text-slate-300",
  NOTIFICATION_ACKNOWLEDGED:  "text-slate-300",
  CASE_CERTIFIED:             "text-emerald-300",
  REPORT_GENERATED:           "text-slate-300",
};

export default function AuditDashboard() {
  const [search, setSearch] = useState("");
  const [resultFilter, setResultFilter] = useState("ALL");
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = AUDIT_EVENTS.filter(e =>
    (resultFilter === "ALL" || e.result === resultFilter) &&
    (e.actor.includes(search) || e.action.includes(search.toUpperCase()) || e.correlation.includes(search) || e.id.includes(search))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-rose-400 px-2 py-0.5 rounded-full bg-rose-950 border border-rose-800/60">
              Auditor · Read-Only
            </span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-rose-400" />
            Compliance & Audit Portal
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable, tamper-evident log of all system transitions, overrides, and administrative actions.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="px-2.5 py-1 rounded-full bg-emerald-950 border border-emerald-800/60 text-emerald-400">
            {AUDIT_EVENTS.filter(e => e.result === "SUCCESS").length} Success
          </span>
          <span className="px-2.5 py-1 rounded-full bg-rose-950 border border-rose-800/60 text-rose-400">
            {AUDIT_EVENTS.filter(e => e.result === "FAILED").length} Failed
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Total Events (7d)", value: AUDIT_EVENTS.length, icon: ClipboardList, color: "slate" },
          { label: "High-Risk Overrides", value: AUDIT_EVENTS.filter(e => e.action.includes("OVERRIDE")).length, icon: AlertOctagon, color: "rose" },
          { label: "Policy Changes", value: AUDIT_EVENTS.filter(e => e.action.includes("MODIFIED")).length, icon: AlertTriangle, color: "amber" },
          { label: "Failures", value: AUDIT_EVENTS.filter(e => e.result === "FAILED").length, icon: XCircle, color: "rose" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
            <div className={`p-2 rounded-lg border ${
              color === "rose"   ? "bg-rose-500/10 border-rose-500/20 text-rose-400" :
              color === "amber"  ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                                   "bg-slate-700/40 border-slate-700 text-slate-400"
            }`}><Icon className="w-4 h-4" /></div>
            <div>
              <div className="text-lg font-bold text-white">{value}</div>
              <div className="text-[11px] text-slate-400">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by actor, action, correlation ID…"
            className="pl-9 pr-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500 placeholder-slate-600 w-72"
          />
        </div>
        <div className="flex gap-1.5">
          {["ALL", "SUCCESS", "FAILED"].map(r => (
            <button key={r} onClick={() => setResultFilter(r)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                resultFilter === r ? "bg-rose-700 text-white" : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
              }`}>{r}</button>
          ))}
        </div>
      </div>

      {/* Audit log */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden">
        <div className="divide-y divide-slate-800/60">
          {filtered.map(e => {
            const R = RESULT_CLS[e.result] || RESULT_CLS.SUCCESS;
            const ResultIcon = R.icon;
            return (
              <div key={e.id} className="hover:bg-slate-800/20 transition-colors">
                <button
                  onClick={() => setExpanded(expanded === e.id ? null : e.id)}
                  className="w-full px-5 py-3.5 flex items-center gap-4 text-left"
                >
                  <ResultIcon className={`w-4 h-4 flex-shrink-0 ${R.cls.split(" ")[0]}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`font-bold text-xs ${ACTION_HIGHLIGHT[e.action] || "text-slate-300"}`}>{e.action}</span>
                      <span className={`text-[10px] font-semibold ${ROLE_CLS[e.role] || "text-slate-400"}`}>{e.role}</span>
                      <span className="text-[10px] text-slate-500">{e.actor}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      {e.entity} #{e.entity_id} · {new Date(e.ts).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${R.cls}`}>{e.result}</span>
                    <span className="text-[10px] text-slate-500 font-mono hidden md:block">{e.id}</span>
                    {expanded === e.id ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                  </div>
                </button>
                {expanded === e.id && (
                  <div className="px-5 pb-5 border-t border-slate-800 pt-3 space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      {[
                        { label: "Event ID", value: e.id },
                        { label: "Correlation ID", value: e.correlation },
                        { label: "IP Address", value: e.ip },
                        { label: "Timestamp", value: new Date(e.ts).toLocaleString() },
                      ].map(({ label, value }) => (
                        <div key={label}>
                          <div className="text-slate-500 text-[10px]">{label}</div>
                          <div className="text-slate-200 font-mono text-[11px] mt-0.5">{value}</div>
                        </div>
                      ))}
                    </div>
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400">
                      <strong className="text-slate-300">Details:</strong> {e.details}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-800/40 text-xs text-rose-400 flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 flex-shrink-0" />
        <span>Audit log is <strong>immutable and tamper-evident</strong>. All events are cryptographically signed and correlation-ID indexed. Read-only access only.</span>
      </div>
    </div>
  );
}
