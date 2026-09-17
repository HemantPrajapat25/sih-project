"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Flame,
  ShieldAlert,
  Cpu,
  CheckCircle2,
  RefreshCw,
  ArrowUpRight,
  SlidersHorizontal,
  Scale,
  Activity,
  AlertTriangle,
  Info
} from "lucide-react";
import { RiskBadge } from "@/components/RiskBadge";
import { StatusChip } from "@/components/StatusChip";
import { api } from "@/lib/api";
import { NumberRecord } from "@/types";

export default function RiskEnginePage() {
  const [numbers, setNumbers] = useState<NumberRecord[]>([]);
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [assessingId, setAssessingId] = useState<string | null>(null);
  const [latestAssessment, setLatestAssessment] = useState<any | null>(null);

  // Simulation State
  const [simBanking, setSimBanking] = useState(true);
  const [simFintech, setSimFintech] = useState(true);
  const [simUnack, setSimUnack] = useState(1);
  const [simDaysElapsed, setSimDaysElapsed] = useState(45);
  const [simCoolingDays, setSimCoolingDays] = useState(60);
  const [simPriorRecycles, setSimPriorRecycles] = useState(1);

  // Fetch real data from backend
  const fetchData = async () => {
    setLoading(true);
    try {
      const [numRes, weightsRes, rulesRes] = await Promise.all([
        api.getNumbers({ limit: 10 }),
        api.getRiskWeights().catch(() => ({ weights: {}, total_weight: 100 })),
        api.getRiskRules().catch(() => []),
      ]);
      setNumbers(Array.isArray(numRes) ? numRes : (numRes as any).items || []);
      setWeights(weightsRes.weights || {});
      setRules(rulesRes || []);
    } catch (err) {
      console.error("Failed to load risk data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunAssessment = async (numberId: string) => {
    setAssessingId(numberId);
    try {
      const assessment = await api.assessNumberRisk(numberId);
      setLatestAssessment(assessment);
      // Refresh numbers list to reflect new score
      await fetchData();
    } catch (err) {
      console.error("Failed to run assessment:", err);
    } finally {
      setAssessingId(null);
    }
  };

  // Dynamic simulation calculations
  const progressRatio = Math.min(simDaysElapsed / simCoolingDays, 1.0);
  const unremediated = (simBanking ? 1 : 0) + (simFintech ? 1 : 0);
  const actualUnremediated = simUnack === 0 ? 0 : unremediated;

  const bScore = actualUnremediated > 0 ? actualUnremediated * 20 : (simBanking || simFintech ? 5 : 0);
  const cScore = Math.round((1.0 - progressRatio) * 30);
  const sScore = Math.min(simUnack * 10, 20);
  const rScore = Math.min(simPriorRecycles * 10, 20);
  const simTotal = Math.min(bScore + cScore + sScore + rScore, 100);

  let simLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" = "LOW";
  if (simTotal <= 25) simLevel = "LOW";
  else if (simTotal <= 55) simLevel = "MEDIUM";
  else if (simTotal <= 79) simLevel = "HIGH";
  else simLevel = "CRITICAL";

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-rose-500" />
            <span>Risk Intelligence Engine</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Explainable, privacy-preserving 10-factor risk scoring with database-driven blocking rules.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Models
        </button>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Configured Factors</span>
            <Scale className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">10 Factors</div>
          <div className="text-[11px] text-slate-500 mt-1">Sum weight: 100 points</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Active Rules</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">{rules.length || 7} Rules</div>
          <div className="text-[11px] text-emerald-400/80 mt-1">DB JSON-DSL active</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>High Risk Monitored</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {numbers.filter((n) => (n.risk_score || 0) >= 55).length} Numbers
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Score ≥ 55</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Privacy Standard</span>
            <CheckCircle2 className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-sky-400">Zero PII</div>
          <div className="text-[11px] text-slate-500 mt-1">HMAC-SHA256 hashed only</div>
        </div>
      </div>

      {/* Latest Live Assessment Result Banner */}
      {latestAssessment && (
        <div className="p-5 rounded-xl border border-rose-500/30 bg-rose-950/20 backdrop-blur-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-rose-400 animate-pulse" />
              <h3 className="text-sm font-semibold text-white">
                Live Assessment Result: {latestAssessment.masked_number}
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Score:</span>
              <span className="text-base font-bold text-rose-400">{latestAssessment.score}/100</span>
              <RiskBadge level={latestAssessment.level} />
            </div>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/80 p-3 rounded-lg border border-slate-800">
            <strong>Recommendation:</strong> {latestAssessment.recommendation} — {latestAssessment.summary}
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            {latestAssessment.factors?.slice(0, 5).map((f: any) => (
              <span key={f.name} className="text-[11px] px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
                {f.name}: <strong className="text-rose-300">+{f.contribution} pts</strong>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Main 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Number Risk Table & Rules (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Numbers Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-200">Decommissioned Numbers Risk Queue</h2>
              <span className="text-xs text-slate-500">{numbers.length} loaded</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3 font-medium">Masked Number</th>
                    <th className="px-4 py-3 font-medium">Carrier</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Risk Score</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {numbers.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                        {loading ? "Loading numbers..." : "No numbers found."}
                      </td>
                    </tr>
                  ) : (
                    numbers.map((n) => (
                      <tr key={n.id} className="hover:bg-slate-800/30 transition">
                        <td className="px-4 py-3 font-mono font-medium text-white">
                          {n.masked_number}
                        </td>
                        <td className="px-4 py-3 text-slate-400">{n.carrier}</td>
                        <td className="px-4 py-3">
                          <StatusChip status={n.status} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white">{n.risk_score || 0}</span>
                            <RiskBadge score={n.risk_score || 0} />
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          <button
                            onClick={() => handleRunAssessment(n.id)}
                            disabled={assessingId === n.id}
                            className="px-2 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-[11px] transition disabled:opacity-50"
                          >
                            {assessingId === n.id ? "Scoring..." : "Assess"}
                          </button>
                          <Link
                            href={`/numbers/${n.id}/risk`}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] border border-slate-700 transition"
                          >
                            <span>Inspect</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Active Rules List */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-400" />
                <span>Evaluated Risk Rules</span>
              </h2>
              <span className="text-[11px] text-slate-500">Evaluated at runtime</span>
            </div>
            <div className="space-y-2">
              {rules.map((rule) => (
                <div
                  key={rule.code}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200">{rule.name}</span>
                      {rule.is_blocking && (
                        <span className="px-1.5 py-0.5 rounded bg-rose-900/50 text-rose-300 border border-rose-800 text-[10px] font-bold">
                          BLOCKING
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono">
                      {rule.condition_expression}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className={`font-semibold ${rule.base_weight > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                      {rule.base_weight > 0 ? `+${rule.base_weight}` : rule.base_weight} pts
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Weights Breakdown & Simulator (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Factor Weights Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm p-4 space-y-3">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Scale className="w-4 h-4 text-indigo-400" />
              <span>Configurable Factor Weights</span>
            </h2>
            <div className="space-y-2.5">
              {Object.entries(weights).map(([k, w]) => (
                <div key={k} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300 capitalize">{k.replace(/_/g, " ")}</span>
                    <span className="font-semibold text-indigo-300">{w}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full rounded-full transition-all"
                      style={{ width: `${w * 4}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Simulation Sandbox */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-rose-400" />
                <span>Risk Simulator</span>
              </h2>
              <RiskBadge level={simLevel} />
            </div>

            {/* Simulated Score Display */}
            <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-center space-y-1">
              <div className="text-3xl font-extrabold text-white">{simTotal}/100</div>
              <div className="text-xs text-slate-400">
                Predicted Status: <strong className="text-slate-200">{simLevel} RISK</strong>
              </div>
            </div>

            {/* Slider Controls */}
            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <div className="flex justify-between text-slate-300">
                  <span>Cooling Elapsed</span>
                  <span className="font-semibold text-white">{simDaysElapsed} / {simCoolingDays} days</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={simCoolingDays}
                  value={simDaysElapsed}
                  onChange={(e) => setSimDaysElapsed(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-300">
                  <span>Unacknowledged Providers</span>
                  <span className="font-semibold text-white">{simUnack}</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={5}
                  value={simUnack}
                  onChange={(e) => setSimUnack(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-300">
                  <span>Prior Recycles</span>
                  <span className="font-semibold text-white">{simPriorRecycles}</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={5}
                  value={simPriorRecycles}
                  onChange={(e) => setSimPriorRecycles(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={simBanking}
                    onChange={(e) => setSimBanking(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-indigo-500 focus:ring-0"
                  />
                  <span>Banking Service Linked</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={simFintech}
                    onChange={(e) => setSimFintech(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-indigo-500 focus:ring-0"
                  />
                  <span>Fintech / UPI Linked</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
