"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ShieldCheck,
  Building2,
  Clock,
  Flame,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Lock,
  RefreshCw,
  Send,
  Sliders,
} from "lucide-react";
import { StatusChip } from "@/components/StatusChip";
import { RiskBadge } from "@/components/RiskBadge";
import { Timeline } from "@/components/Timeline";
import { RoleGuard } from "@/components/RoleGuard";
import { api } from "@/lib/api";
import { NumberDetail } from "@/types";

export default function NumberDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [number, setNumber] = useState<NumberDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [overrideScore, setOverrideScore] = useState(30);
  const [overrideReason, setOverrideReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadDetail() {
    setLoading(true);
    try {
      const data = await api.getNumberDetail(id);
      setNumber(data);
      setOverrideScore(data.risk_score);
    } catch (err) {
      console.error("Failed to load number detail:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (id) loadDetail();
  }, [id]);

  async function handleAcknowledgeNotification(notifId: string) {
    try {
      await api.acknowledgeNotification(notifId, "REMEDIATED");
      await loadDetail();
    } catch (err: any) {
      alert("Failed to acknowledge: " + err.message);
    }
  }

  async function handleOverrideSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!overrideReason.trim()) {
      alert("Please provide an engineering reason for the risk override.");
      return;
    }
    setIsSubmitting(true);
    try {
      await api.overrideRiskScore(id, overrideScore, overrideReason);
      setOverrideOpen(false);
      await loadDetail();
    } catch (err: any) {
      alert("Override failed: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return <div className="py-20 text-center text-slate-500 text-xs">Loading number lifecycle record...</div>;
  }

  if (!number) {
    return (
      <div className="py-20 text-center text-slate-500 text-xs space-y-2">
        <p>Number record not found.</p>
        <Link href="/numbers" className="text-cyan-400 hover:underline">
          Return to directory
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Link
            href="/numbers"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold font-mono tracking-tight text-white">
                {number.masked_number}
              </h1>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                {number.carrier}
              </span>
              <StatusChip status={number.status} />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Record ID: <span className="font-mono text-slate-500">{number.id}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadDetail}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white"
            title="Refresh record"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <RoleGuard permission="risk.override">
            <button
              onClick={() => setOverrideOpen(true)}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              <span>Risk Override</span>
            </button>
          </RoleGuard>
        </div>
      </div>

      {/* Lifecycle Progression Timeline */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
        <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
          Lifecycle State Progression
        </h2>
        <Timeline
          status={number.status}
          decommissionDate={number.decommissioned_at}
          coolingEndDate={number.cooling_end_date}
          eligibility={number.allocation_eligibility}
          remediationPct={number.remediation_percentage}
        />
      </div>

      {/* Grid: Risk Evaluation & Allocation Recommendation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Risk Analysis & Factors */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Engine Breakdown */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <Flame className="w-4 h-4 text-rose-400" />
                  <span>Risk Engine Assessment</span>
                </h2>
                <p className="text-xs text-slate-400">Algorithmic evaluation of residual reassignment liability</p>
              </div>
              <RiskBadge score={number.risk_score} level={number.risk_level} />
            </div>

            {/* Factors list */}
            <div className="space-y-2.5 pt-2">
              {number.risk_factors && number.risk_factors.length > 0 ? (
                number.risk_factors.map((f, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-slate-200">{f.name}</div>
                      <div className="text-[11px] text-slate-400">{f.description}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-cyan-400">+{f.score_contribution} pts</div>
                      <div className="text-[10px] text-slate-500">Weight: {f.weight}%</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 text-xs">Standard risk parameters applied.</div>
              )}
            </div>
          </div>

          {/* Provider Notification & Remediation Table */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-purple-400" />
                  <span>Participating Service Providers & Remediation</span>
                </h2>
                <p className="text-xs text-slate-400">Cryptographic challenge unlinking status per ecosystem partner</p>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {number.remediation_percentage}% Remediated
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                    <th className="py-2.5 px-3">Provider</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Pseudonym Ref</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Sent Time</th>
                    <th className="py-2.5 px-3 text-right">Remediation Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {number.notifications && number.notifications.length > 0 ? (
                    number.notifications.map((n) => (
                      <tr key={n.id} className="hover:bg-slate-800/30">
                        <td className="py-3 px-3 font-semibold text-slate-200">{n.provider_name}</td>
                        <td className="py-3 px-3">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                            {n.provider_category}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-mono text-cyan-400 text-[11px]">
                          {n.pseudonym_ref}
                        </td>
                        <td className="py-3 px-3">
                          <StatusChip status={n.status} size="sm" />
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-[11px]">
                          {new Date(n.sent_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-3 text-right">
                          {n.status !== "REMEDIATED" ? (
                            <RoleGuard
                              permission="notifications.acknowledge"
                              fallback={<span className="text-slate-500 text-[11px]">Pending Partner Ack</span>}
                            >
                              <button
                                onClick={() => handleAcknowledgeNotification(n.id)}
                                className="px-2.5 py-1 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 text-[11px] font-semibold cursor-pointer"
                              >
                                Simulate Ack
                              </button>
                            </RoleGuard>
                          ) : (
                            <span className="text-emerald-400 flex items-center justify-end gap-1 text-[11px]">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Remediated</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-slate-500">
                        No provider notifications dispatched for this record.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Col: Allocation Readiness & Audit History */}
        <div className="space-y-6">
          {/* Allocation Recommendation Card */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Carrier Allocation Recommendation</span>
            </h2>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Current Eligibility</span>
                <StatusChip status={number.allocation_eligibility} />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Cooling Expiry</span>
                <span className="font-semibold text-slate-200">
                  {new Date(number.cooling_end_date).toLocaleDateString()}
                </span>
              </div>

              {number.hold_reason && (
                <div className="p-2.5 rounded bg-rose-950/50 border border-rose-900/60 text-xs text-rose-300">
                  <strong>Hold Reason:</strong> {number.hold_reason}
                </div>
              )}

              <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
                {number.allocation_eligibility === "ELIGIBLE"
                  ? "Approved for carrier reallocation to a new subscriber without privacy collision risk."
                  : number.allocation_eligibility === "BLOCKED"
                  ? "Reallocation blocked due to active high-risk banking/fintech links. Requires provider remediation."
                  : "Retain in cooling quarantine until the mandatory quarantine window expires."}
              </p>
            </div>
          </div>

          {/* Record Audit Events Stream */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Audit Trail</span>
            </h2>

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {number.audit_events && number.audit_events.length > 0 ? (
                number.audit_events.map((a) => (
                  <div key={a.id} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-300">{a.action}</span>
                      <span className="text-[10px] text-slate-500">
                        {new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">{a.details || a.actor_email}</p>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 text-xs py-4 text-center">No audit logs for this number.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Manual Risk Override Modal */}
      {overrideOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Administrative Risk Override</span>
            </h2>
            <p className="text-xs text-slate-400">
              Only authorized TELECOM_ADMIN users can adjust calculated risk scores. This action is permanently logged to compliance audit trails.
            </p>

            <form onSubmit={handleOverrideSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 mb-1 font-medium">New Risk Score (0 - 100)</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={overrideScore}
                  onChange={(e) => setOverrideScore(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">Mandatory Justification / Reason</label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Verified manual subscriber waiver and banking dissociation document #DOC-892"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setOverrideOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? "Overriding..." : "Apply Override"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
