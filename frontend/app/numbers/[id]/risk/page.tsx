"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Flame,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Scale,
  Cpu,
  Layers,
  FileCheck2,
  ShieldX
} from "lucide-react";
import { RiskBadge } from "@/components/RiskBadge";
import { StatusChip } from "@/components/StatusChip";
import { api } from "@/lib/api";

export default function NumberRiskDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [assessment, setAssessment] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reassessing, setReassessing] = useState(false);

  const loadAssessment = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.assessNumberRisk(id);
      setAssessment(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load risk assessment");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadAssessment();
    }
  }, [id]);

  const handleReassess = async () => {
    setReassessing(true);
    try {
      const data = await api.assessNumberRisk(id);
      setAssessment(data);
    } catch (err: any) {
      alert("Assessment failed: " + err.message);
    } finally {
      setReassessing(false);
    }
  };

  const score = assessment?.score || 0;
  // Circumference for a radius 40 circle = 2 * PI * 40 = 251.3
  const strokeDashoffset = 251.3 - (251.3 * score) / 100;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header with back link */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <Link
            href={`/numbers/${id}`}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Flame className="w-5 h-5 text-rose-500" />
              <span>Risk Assessment Report</span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Comprehensive 10-factor audit trail for number ID: <code className="font-mono text-slate-300">{id}</code>
            </p>
          </div>
        </div>

        <button
          onClick={handleReassess}
          disabled={reassessing || loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/20 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${reassessing ? "animate-spin" : ""}`} />
          <span>{reassessing ? "Re-evaluating..." : "Re-calculate Score"}</span>
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-rose-500 mb-3" />
          <p className="text-sm">Running privacy-preserving factor calculations...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-xl border border-rose-800/40 bg-rose-950/20 text-rose-300 text-sm space-y-2">
          <div className="font-semibold flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>Could not complete assessment</span>
          </div>
          <p className="text-xs text-slate-400">{error}</p>
        </div>
      ) : assessment ? (
        <div className="space-y-6">
          {/* Top Banner: Score Gauge + Recommendation */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
            {/* SVG Meter (4 cols) */}
            <div className="md:col-span-4 flex flex-col items-center justify-center p-4 border-b md:border-b-0 md:border-r border-slate-800/80">
              <div className="relative w-40 h-40 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    className="text-slate-800 fill-none"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    strokeDasharray={251.3}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    className={`transition-all duration-1000 fill-none ${
                      score <= 25
                        ? "text-emerald-500"
                        : score <= 55
                        ? "text-amber-500"
                        : score <= 79
                        ? "text-rose-500"
                        : "text-red-600"
                    }`}
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className="text-3xl font-extrabold text-white">{score}</span>
                  <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                    Score / 100
                  </span>
                </div>
              </div>
              <div className="mt-3">
                <RiskBadge level={assessment.level} />
              </div>
            </div>

            {/* Recommendation & Overview (8 cols) */}
            <div className="md:col-span-8 flex flex-col justify-center space-y-4">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                  Allocation Recommendation
                </span>
                <div className="flex items-center gap-2 mt-1">
                  {assessment.is_blocked ? (
                    <ShieldX className="w-6 h-6 text-rose-500 flex-shrink-0" />
                  ) : (
                    <ShieldCheck className="w-6 h-6 text-emerald-500 flex-shrink-0" />
                  )}
                  <h2 className="text-lg font-bold text-white tracking-tight">
                    {assessment.recommendation}
                  </h2>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed space-y-1">
                <div className="font-semibold text-slate-200">Assessment Summary:</div>
                <p>{assessment.summary}</p>
                {assessment.detail_explanation && (
                  <p className="text-slate-400 pt-1">{assessment.detail_explanation}</p>
                )}
              </div>

              {assessment.is_blocked && (
                <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Reallocation Blocked by Policy Rules:</span>
                    <ul className="list-disc list-inside mt-1 text-[11px] text-rose-200/80">
                      {assessment.blocking_rules?.map((br: string, i: number) => (
                        <li key={i}>{br}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Factor Breakdown (10 Factors) */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Independent 10-Factor Score Contribution</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {assessment.factors?.map((f: any) => (
                <div
                  key={f.name}
                  className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200 capitalize">
                      {f.name.replace(/_/g, " ")}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-slate-400">Contribution:</span>
                      <span className="font-bold text-rose-400">+{f.contribution} pts</span>
                      <span className="text-[10px] text-slate-500">/ max {f.weight}</span>
                    </div>
                  </div>

                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-rose-500 h-full rounded-full transition-all"
                      style={{ width: `${(f.contribution / Math.max(f.weight, 1)) * 100}%` }}
                    />
                  </div>

                  <p className="text-[11px] text-slate-400 leading-snug">{f.explanation}</p>

                  {f.evidence && Object.keys(f.evidence).length > 0 && (
                    <div className="text-[10px] font-mono text-slate-500 bg-slate-950/60 p-1.5 rounded border border-slate-800/60">
                      Evidence: {JSON.stringify(f.evidence)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Evaluated Rules Matrix */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>Database Rule Engine Evaluation Matrix</span>
            </h3>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3 font-medium">Rule</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Policy Type</th>
                    <th className="px-4 py-3 font-medium">Score Impact</th>
                    <th className="px-4 py-3 font-medium">Evaluation Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {assessment.rules_applied?.map((r: any) => (
                    <tr key={r.code} className="hover:bg-slate-800/20 transition">
                      <td className="px-4 py-3 font-medium text-white">{r.name}</td>
                      <td className="px-4 py-3">
                        {r.triggered ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-900/40 text-rose-300 border border-rose-800">
                            TRIGGERED
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
                            PASSED
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {r.is_blocking ? (
                          <span className="text-[11px] font-semibold text-rose-400">BLOCKING</span>
                        ) : (
                          <span className="text-[11px] text-slate-400">ADVISORY</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`font-semibold ${
                            r.triggered && r.impact > 0
                              ? "text-rose-400"
                              : r.triggered && r.impact < 0
                              ? "text-emerald-400"
                              : "text-slate-500"
                          }`}
                        >
                          {r.triggered ? `${r.impact > 0 ? "+" : ""}${r.impact} pts` : "0 pts"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-[11px]">{r.evidence}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
