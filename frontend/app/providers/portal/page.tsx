"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Building2,
  Clock,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  Check,
  Send
} from "lucide-react";
import { api } from "@/lib/api";
import { ServiceProvider, NotificationRecord } from "@/types";

export default function ProviderPortalPage() {
  const [providers, setProviders] = useState<ServiceProvider[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string>("");
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const pList = await api.getProviders();
      setProviders(pList);
      if (pList.length > 0 && !selectedProviderId) {
        setSelectedProviderId(pList[0].id);
      }
    } catch (err) {
      console.error("Failed to load providers:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadNotifications = async () => {
    try {
      const notifs = await api.getNotifications(selectedProviderId ? { provider_id: selectedProviderId } : undefined);
      setNotifications(notifs);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedProviderId) {
      loadNotifications();
    }
  }, [selectedProviderId]);

  const handleUpdateStatus = async (id: string, newStatus: "ACKNOWLEDGED" | "REMEDIATED") => {
    setActingId(id);
    try {
      await api.acknowledgeNotification(id, newStatus);
      await loadNotifications();
    } catch (err: any) {
      alert("Status update failed: " + err.message);
    } finally {
      setActingId(null);
    }
  };

  const selectedProvider = providers.find((p) => p.id === selectedProviderId);

  // Compute metrics
  const pendingCount = notifications.filter((n) => n.status === "SENT" || n.status === "PENDING").length;
  const ackCount = notifications.filter((n) => n.status === "ACKNOWLEDGED").length;
  const remediatedCount = notifications.filter((n) => n.status === "REMEDIATED").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <span>Digital Partner Self-Remediation Portal</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Scoped access for participating digital service providers to acknowledge decommissions and certify customer unlinking.
          </p>
        </div>

        {/* Provider Selector */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400">Viewing as:</label>
          <div className="relative">
            <select
              value={selectedProviderId}
              onChange={(e) => setSelectedProviderId(e.target.value)}
              className="appearance-none bg-slate-900 border border-slate-700 text-white text-xs font-semibold py-1.5 pl-3 pr-8 rounded-lg focus:outline-none focus:border-indigo-500"
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.category})
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          <button
            onClick={loadNotifications}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Provider Details & SLA Banner */}
      {selectedProvider && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs text-slate-400">Partner Category</div>
            <div className="text-lg font-bold text-white mt-0.5">{selectedProvider.category}</div>
            <div className="text-[11px] text-slate-500 mt-1">Tier unlinking profile</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs text-slate-400">Pending Actions</div>
            <div className="text-lg font-bold text-amber-400 mt-0.5">{pendingCount} Unlinked</div>
            <div className="text-[11px] text-slate-500 mt-1">Requires partner action</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs text-slate-400">Acknowledged</div>
            <div className="text-lg font-bold text-sky-400 mt-0.5">{ackCount} In Progress</div>
            <div className="text-[11px] text-slate-500 mt-1">Within SLA deadline</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs text-slate-400">Remediated & Clear</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">{remediatedCount} Severed</div>
            <div className="text-[11px] text-emerald-500/80 mt-1">Zero residual risk</div>
          </div>
        </div>
      )}

      {/* Notifications / Remediation Queue Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Pending Decommission Notices & Unlinking Tickets</h2>
          <span className="text-xs text-slate-500">{notifications.length} notices for this provider</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-medium">Pseudonym Ref</th>
                <th className="px-4 py-3 font-medium">Channel</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Dispatched</th>
                <th className="px-4 py-3 font-medium text-right">Certification Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {notifications.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-slate-500">
                    No active decommission notices queued for this provider.
                  </td>
                </tr>
              ) : (
                notifications.map((n) => (
                  <tr key={n.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-mono font-medium text-white">
                      {n.pseudonym_ref}
                    </td>
                    <td className="px-4 py-3 text-slate-400">{n.notification_type || "WEBHOOK"}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          n.status === "REMEDIATED"
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800"
                            : n.status === "ACKNOWLEDGED"
                            ? "bg-sky-950/60 text-sky-300 border border-sky-800"
                            : "bg-amber-950/60 text-amber-300 border border-amber-800"
                        }`}
                      >
                        {n.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {n.sent_at ? new Date(n.sent_at).toLocaleDateString() : "Pending"}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      {n.status !== "REMEDIATED" ? (
                        <>
                          {n.status !== "ACKNOWLEDGED" && (
                            <button
                              onClick={() => handleUpdateStatus(n.id, "ACKNOWLEDGED")}
                              disabled={actingId === n.id}
                              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-[11px] transition disabled:opacity-50"
                            >
                              Acknowledge
                            </button>
                          )}
                          <button
                            onClick={() => handleUpdateStatus(n.id, "REMEDIATED")}
                            disabled={actingId === n.id}
                            className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-[11px] transition disabled:opacity-50 shadow-sm"
                          >
                            {actingId === n.id ? "Updating..." : "Certify Unlinked"}
                          </button>
                        </>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                          <Check className="w-3.5 h-3.5" />
                          Remediated
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
    </div>
  );
}
