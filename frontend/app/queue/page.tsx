"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Clock, AlertTriangle, ShieldCheck, Flame, ArrowRight, Eye, RefreshCw } from "lucide-react";
import { StatusChip } from "@/components/StatusChip";
import { RiskBadge } from "@/components/RiskBadge";
import { api } from "@/lib/api";
import { NumberRecord } from "@/types";

export default function DecommissioningQueuePage() {
  const [numbers, setNumbers] = useState<NumberRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"NEW" | "EXPIRING_SOON" | "HIGH_RISK" | "PENDING_RESPONSE">("EXPIRING_SOON");

  async function loadData() {
    setLoading(true);
    try {
      const data = await api.getNumbers();
      setNumbers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const now = new Date().getTime();

  // Filter queues
  const newNumbers = numbers.filter((n) => n.status === "DECOMMISSIONED");
  const highRiskNumbers = numbers.filter((n) => n.risk_level === "HIGH" || n.risk_level === "CRITICAL");
  const pendingResponse = numbers.filter((n) => n.remediation_percentage < 100);
  const expiringSoon = numbers.filter((n) => {
    const end = new Date(n.cooling_end_date).getTime();
    const daysLeft = (end - now) / (1000 * 60 * 60 * 24);
    return daysLeft >= -10 && daysLeft <= 15;
  });

  const tabCounts = {
    EXPIRING_SOON: expiringSoon.length,
    HIGH_RISK: highRiskNumbers.length,
    PENDING_RESPONSE: pendingResponse.length,
    NEW: newNumbers.length,
  };

  const currentList =
    activeTab === "EXPIRING_SOON"
      ? expiringSoon
      : activeTab === "HIGH_RISK"
      ? highRiskNumbers
      : activeTab === "PENDING_RESPONSE"
      ? pendingResponse
      : newNumbers;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-amber-400" />
            <span>Decommissioning Action Queue</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Operational triage queues for cooling expirations, unresolved provider alerts, and high-risk holds.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white self-start"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("EXPIRING_SOON")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer ${
            activeTab === "EXPIRING_SOON"
              ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <span>Cooling Expiry Approaching</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px]">
            {tabCounts.EXPIRING_SOON}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("HIGH_RISK")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer ${
            activeTab === "HIGH_RISK"
              ? "bg-rose-500/15 text-rose-300 border border-rose-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <span>High Risk Quarantine</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px]">
            {tabCounts.HIGH_RISK}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("PENDING_RESPONSE")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer ${
            activeTab === "PENDING_RESPONSE"
              ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <span>Provider Responses Pending</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px]">
            {tabCounts.PENDING_RESPONSE}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("NEW")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer ${
            activeTab === "NEW"
              ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
        >
          <span>Newly Decommissioned</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px]">
            {tabCounts.NEW}
          </span>
        </button>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
              <th className="py-3 px-4">Masked Number</th>
              <th className="py-3 px-3">Carrier</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3">Cooling Expiry</th>
              <th className="py-3 px-3">Risk Rating</th>
              <th className="py-3 px-3">Remediation Progress</th>
              <th className="py-3 px-3">Eligibility Recommendation</th>
              <th className="py-3 px-3 text-right">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-slate-500">
                  Loading queue records...
                </td>
              </tr>
            ) : currentList.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-slate-500">
                  Queue is clear. Zero numbers pending in this category.
                </td>
              </tr>
            ) : (
              currentList.map((n) => (
                <tr key={n.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-semibold text-slate-100">
                    {n.masked_number}
                  </td>
                  <td className="py-3.5 px-3 font-medium text-slate-300">{n.carrier}</td>
                  <td className="py-3.5 px-3">
                    <StatusChip status={n.status} size="sm" />
                  </td>
                  <td className="py-3.5 px-3 text-slate-300 font-medium">
                    {new Date(n.cooling_end_date).toLocaleDateString()}
                  </td>
                  <td className="py-3.5 px-3">
                    <RiskBadge score={n.risk_score} level={n.risk_level} />
                  </td>
                  <td className="py-3.5 px-3">
                    <span className="text-slate-300 font-semibold">{n.remediation_percentage}%</span>
                  </td>
                  <td className="py-3.5 px-3">
                    <StatusChip status={n.allocation_eligibility} size="sm" />
                  </td>
                  <td className="py-3.5 px-3 text-right">
                    <Link
                      href={`/numbers/${n.id}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs"
                    >
                      <Eye className="w-3 h-3" />
                      <span>Review</span>
                    </Link>
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
