"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  Upload,
  RefreshCw,
  Eye,
  Hash,
  Clock,
  CheckCircle2,
  ShieldAlert,
} from "lucide-react";
import { StatusChip } from "@/components/StatusChip";
import { RiskBadge } from "@/components/RiskBadge";
import { ImportModal } from "@/components/ImportModal";
import { api } from "@/lib/api";
import { NumberRecord } from "@/types";

export default function NumbersPage() {
  const [numbers, setNumbers] = useState<NumberRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [carrier, setCarrier] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [riskLevel, setRiskLevel] = useState("ALL");
  const [importOpen, setImportOpen] = useState(false);

  async function loadNumbers() {
    setLoading(true);
    try {
      const data = await api.getNumbers({
        search: search || undefined,
        carrier: carrier !== "ALL" ? carrier : undefined,
        status: status !== "ALL" ? status : undefined,
        risk_level: riskLevel !== "ALL" ? riskLevel : undefined,
      });
      setNumbers(data);
    } catch (err) {
      console.error("Failed to load numbers:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNumbers();
  }, [carrier, status, riskLevel]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Hash className="w-5 h-5 text-cyan-400" />
            <span>Mobile Number Inventory</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Privacy-masked decommissioned subscriber records, cooling quarantine trackers, and risk ratings.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadNumbers}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white"
            title="Refresh table"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setImportOpen(true)}
            className="px-3.5 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs flex items-center gap-1.5 transition-colors cursor-pointer shadow-md shadow-cyan-500/20"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Import Numbers</span>
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search masked number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadNumbers()}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Carrier Filter */}
        <div>
          <select
            value={carrier}
            onChange={(e) => setCarrier(e.target.value)}
            className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Carriers (Jio, Airtel, Vi, BSNL)</option>
            <option value="Jio">Jio Infocomm</option>
            <option value="Airtel">Bharti Airtel</option>
            <option value="Vi">Vodafone Idea (Vi)</option>
            <option value="BSNL">BSNL</option>
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Lifecycle Statuses</option>
            <option value="DECOMMISSIONED">Decommissioned</option>
            <option value="COOLING_HOLD">In Cooling Hold</option>
            <option value="MANUAL_REVIEW">Manual Review</option>
            <option value="ELIGIBLE">Eligible for Reallocation</option>
            <option value="REALLOCATED">Reallocated</option>
          </select>
        </div>

        {/* Risk Level Filter */}
        <div>
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="CRITICAL">Critical Risk</option>
          </select>
        </div>
      </div>

      {/* Numbers Data Table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4">Masked Number</th>
                <th className="py-3 px-3">Carrier</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Decommission Date</th>
                <th className="py-3 px-3">Cooling End Date</th>
                <th className="py-3 px-3">Risk Rating</th>
                <th className="py-3 px-3">Providers / Remediated</th>
                <th className="py-3 px-3">Eligibility</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    Loading mobile number lifecycle records...
                  </td>
                </tr>
              ) : numbers.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    No matching numbers found. Try adjusting filters or import numbers.
                  </td>
                </tr>
              ) : (
                numbers.map((n) => (
                  <tr
                    key={n.id}
                    className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                  >
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-100 flex items-center gap-2">
                      <span className="text-cyan-400 font-normal">#</span>
                      <span>{n.masked_number}</span>
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="font-medium text-slate-300">{n.carrier}</span>
                    </td>
                    <td className="py-3.5 px-3">
                      <StatusChip status={n.status} size="sm" />
                    </td>
                    <td className="py-3.5 px-3 text-slate-400">
                      {new Date(n.decommissioned_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-3 text-slate-300 font-medium">
                      {new Date(n.cooling_end_date).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-3">
                      <RiskBadge score={n.risk_score} level={n.risk_level} />
                    </td>
                    <td className="py-3.5 px-3">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300 font-medium">
                          {n.remediation_percentage}%
                        </span>
                        <div className="w-14 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-cyan-400 rounded-full"
                            style={{ width: `${n.remediation_percentage}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-slate-500">({n.provider_count})</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-3">
                      <StatusChip status={n.allocation_eligibility} size="sm" />
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <Link
                        href={`/numbers/${n.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <ImportModal
        isOpen={importOpen}
        onClose={() => setImportOpen(false)}
        onSuccess={() => {
          setImportOpen(false);
          loadNumbers();
        }}
      />
    </div>
  );
}
