"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { BellRing, CheckCircle2, Clock, RefreshCw, Eye, Send } from "lucide-react";
import { StatusChip } from "@/components/StatusChip";
import { RoleGuard } from "@/components/RoleGuard";
import { api } from "@/lib/api";
import { NotificationRecord } from "@/types";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");

  async function loadData() {
    setLoading(true);
    try {
      const data = await api.getNotifications({
        status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      setNotifications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  async function handleAcknowledge(id: string) {
    try {
      await api.acknowledgeNotification(id, "REMEDIATED");
      await loadData();
    } catch (err: any) {
      alert("Failed: " + err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <BellRing className="w-5 h-5 text-cyan-400" />
            <span>Digital Provider Notification Dispatch Hub</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Log of unlinking alerts dispatched to registered banks, fintechs, and services with cryptographic challenge references.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
          >
            <option value="ALL">All Notification Statuses</option>
            <option value="SENT">Sent (Awaiting Ack)</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="REMEDIATED">Remediated</option>
            <option value="FAILED">Failed</option>
          </select>

          <button
            onClick={loadData}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Notifications Table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
              <th className="py-3 px-4">Notification Ref</th>
              <th className="py-3 px-3">Provider</th>
              <th className="py-3 px-3">Category</th>
              <th className="py-3 px-3">Masked Number</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3">Sent Time</th>
              <th className="py-3 px-3">Acknowledged</th>
              <th className="py-3 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-slate-500">
                  Loading provider dispatch log...
                </td>
              </tr>
            ) : notifications.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-slate-500">
                  No notifications matching filter criteria.
                </td>
              </tr>
            ) : (
              notifications.map((n) => (
                <tr key={n.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono text-cyan-400 font-semibold">
                    {n.pseudonym_ref}
                  </td>
                  <td className="py-3 px-3 font-semibold text-slate-200">{n.provider_name}</td>
                  <td className="py-3 px-3">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      {n.provider_category}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">
                    {n.masked_number || "--"}
                  </td>
                  <td className="py-3 px-3">
                    <StatusChip status={n.status} size="sm" />
                  </td>
                  <td className="py-3 px-3 text-slate-400">
                    {new Date(n.sent_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-slate-400">
                    {n.acknowledged_at ? new Date(n.acknowledged_at).toLocaleTimeString() : "--"}
                  </td>
                  <td className="py-3 px-3 text-right">
                    {n.status !== "REMEDIATED" ? (
                      <RoleGuard
                        permission="notifications.acknowledge"
                        fallback={<span className="text-slate-500 text-[10px]">Awaiting Partner</span>}
                      >
                        <button
                          onClick={() => handleAcknowledge(n.id)}
                          className="px-2.5 py-1 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 text-[11px] font-semibold cursor-pointer"
                        >
                          Remediate
                        </button>
                      </RoleGuard>
                    ) : (
                      <span className="text-emerald-400 flex items-center justify-end gap-1 text-[11px]">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Done</span>
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
