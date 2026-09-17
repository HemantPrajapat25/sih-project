"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { CheckCircle2, AlertTriangle, ShieldAlert, Lock, Clock, ArrowRight, RefreshCw, Send } from "lucide-react";
import { StatusChip } from "@/components/StatusChip";
import { RoleGuard } from "@/components/RoleGuard";
import { api } from "@/lib/api";
import { ReadinessSummary, NumberRecord } from "@/types";

export default function AllocationReadinessPage() {
  const [summary, setSummary] = useState<ReadinessSummary | null>(null);
  const [eligibleNumbers, setEligibleNumbers] = useState<NumberRecord[]>([]);
  const [blockedNumbers, setBlockedNumbers] = useState<NumberRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [releasing, setReleasing] = useState(false);
  const [releaseSuccess, setReleaseSuccess] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [sum, nums] = await Promise.all([
        api.getReadinessSummary(),
        api.getNumbers({ limit: 100 }),
      ]);
      setSummary(sum);
      setEligibleNumbers(nums.filter((n) => n.allocation_eligibility === "ELIGIBLE"));
      setBlockedNumbers(nums.filter((n) => n.allocation_eligibility === "BLOCKED" || n.allocation_eligibility === "MANUAL_REVIEW_REQUIRED"));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleBatchRelease() {
    if (eligibleNumbers.length === 0) return;
    setReleasing(true);
    setReleaseSuccess(null);
    try {
      const ids = eligibleNumbers.map((n) => n.id);
      const res = await api.batchReleaseNumbers(ids, "Batch release to carrier pool");
      setReleaseSuccess(`Successfully approved & released ${res.released_count} numbers for reallocation.`);
      await loadData();
    } catch (err: any) {
      alert("Release failed: " + err.message);
    } finally {
      setReleasing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span>Subscriber Allocation Readiness</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit-grade clearance decision engine certifying when a recycled number is legally safe for reallocation.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white self-start"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {releaseSuccess && (
        <div className="p-4 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{releaseSuccess}</span>
        </div>
      )}

      {/* Decision Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase">Recommended Eligible</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 mt-2">
            {summary?.total_eligible ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Cooling elapsed & zero active alerts</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase">Cooling Quarantine</span>
            <span className="w-2 h-2 rounded-full bg-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400 mt-2">
            {summary?.total_cooling_hold ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Statutory days remaining</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase">Hard Blocked</span>
            <span className="w-2 h-2 rounded-full bg-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400 mt-2">
            {summary?.total_blocked ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Active banking / fintech alerts</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase">Manual Review</span>
            <span className="w-2 h-2 rounded-full bg-orange-400" />
          </div>
          <div className="text-3xl font-extrabold text-orange-400 mt-2">
            {summary?.total_manual_review ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Disputed ownership / high residual</p>
        </div>
      </div>

      {/* Action Bar for Batch Release */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold text-white">Carrier Reallocation Release Pool</h2>
          <p className="text-xs text-slate-400">
            {eligibleNumbers.length} numbers have passed all statutory checks and are cleared for release to telecom sales inventory.
          </p>
        </div>

        <RoleGuard
          permission="numbers.reallocate"
          fallback={<span className="text-slate-500 text-xs">Approval requires TELECOM_ADMIN</span>}
        >
          <button
            onClick={handleBatchRelease}
            disabled={releasing || eligibleNumbers.length === 0}
            className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold flex items-center gap-2 cursor-pointer shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>{releasing ? "Approving Release..." : `Approve & Release (${eligibleNumbers.length})`}</span>
          </button>
        </RoleGuard>
      </div>

      {/* Blocked Reasons Breakdown */}
      {summary && summary.blocked_reasons && Object.keys(summary.blocked_reasons).length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Active Block Justification Hierarchy
          </h2>
          <div className="space-y-2 text-xs">
            {Object.entries(summary.blocked_reasons).map(([reason, count]) => (
              <div
                key={reason}
                className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between"
              >
                <div className="flex items-center gap-2 text-rose-300">
                  <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                  <span>{reason}</span>
                </div>
                <span className="font-semibold text-white px-2 py-0.5 rounded bg-slate-800">
                  {count} Numbers Blocked
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
