"use client";

import React, { useState, useEffect } from "react";
import { FileText, Search, ShieldCheck, RefreshCw, Hash, Eye } from "lucide-react";
import { api } from "@/lib/api";
import { AuditRecord } from "@/types";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditRecord | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const data = await api.getAuditLogs({ search: search || undefined, limit: 100 });
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            <span>Immutable Compliance Audit Trail</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Tamper-evident logs of all carrier number state transitions, administrative overrides, and provider notifications.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search action or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadData()}
              className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <button
            onClick={loadData}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
              <th className="py-3 px-4">Correlation ID</th>
              <th className="py-3 px-3">Actor / Role</th>
              <th className="py-3 px-3">Organization</th>
              <th className="py-3 px-3">Action</th>
              <th className="py-3 px-3">Entity Type</th>
              <th className="py-3 px-3">Timestamp</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-slate-500">
                  Loading audit log stream...
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-slate-500">
                  No audit logs matching search query.
                </td>
              </tr>
            ) : (
              logs.map((a) => (
                <tr key={a.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-cyan-400 font-semibold text-[11px]">
                    {a.correlation_id}
                  </td>
                  <td className="py-3.5 px-3">
                    <div className="font-semibold text-slate-200">{a.actor_email}</div>
                    <div className="text-[10px] text-slate-400">{a.actor_role}</div>
                  </td>
                  <td className="py-3.5 px-3 text-slate-300 font-medium">{a.organization_name}</td>
                  <td className="py-3.5 px-3">
                    <span className="font-semibold text-slate-200 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {a.action}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-slate-400 text-[11px] uppercase">
                    {a.entity_type}
                  </td>
                  <td className="py-3.5 px-3 text-slate-400 text-[11px]">
                    {new Date(a.timestamp).toLocaleString()}
                  </td>
                  <td className="py-3.5 px-3">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                      {a.result}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-right">
                    <button
                      onClick={() => setSelectedLog(a)}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Audit Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                <span>Audit Entry Record</span>
              </h2>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                Close
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Correlation ID:</span>
                <span className="font-mono text-cyan-400">{selectedLog.correlation_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Actor Email:</span>
                <span className="font-semibold text-slate-200">{selectedLog.actor_email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Actor Role:</span>
                <span className="font-semibold text-slate-200">{selectedLog.actor_role}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Organization:</span>
                <span className="text-slate-200">{selectedLog.organization_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">IP Metadata:</span>
                <span className="font-mono text-slate-400">{selectedLog.ip_address}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Timestamp:</span>
                <span className="text-slate-200">{new Date(selectedLog.timestamp).toISOString()}</span>
              </div>

              <div>
                <span className="text-slate-400 block mb-1">Payload / State Diff:</span>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 whitespace-pre-wrap break-all">
                  {selectedLog.details || "No extended details recorded for this transition."}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
