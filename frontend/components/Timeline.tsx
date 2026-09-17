import React from "react";
import { CheckCircle2, Clock, ShieldAlert, ArrowRight, ShieldCheck } from "lucide-react";

interface TimelineProps {
  status: string;
  decommissionDate: string;
  coolingEndDate: string;
  eligibility: string;
  remediationPct: number;
}

export function Timeline({
  status,
  decommissionDate,
  coolingEndDate,
  eligibility,
  remediationPct,
}: TimelineProps) {
  const steps = [
    {
      title: "Decommissioned",
      desc: new Date(decommissionDate).toLocaleDateString(),
      completed: true,
      current: false,
    },
    {
      title: "Provider Dispatched",
      desc: `${remediationPct}% remediated`,
      completed: remediationPct > 0 || status !== "DECOMMISSIONED",
      current: status === "NOTIFYING_PROVIDERS",
    },
    {
      title: "Cooling Period",
      desc: `Until ${new Date(coolingEndDate).toLocaleDateString()}`,
      completed: new Date() >= new Date(coolingEndDate),
      current: status === "COOLING_HOLD",
    },
    {
      title: "Risk Evaluation",
      desc: eligibility === "BLOCKED" ? "Blocked by Banking" : "Risk assessed",
      completed: eligibility !== "BLOCKED" && eligibility !== "MANUAL_REVIEW_REQUIRED",
      current: eligibility === "MANUAL_REVIEW_REQUIRED" || eligibility === "BLOCKED",
    },
    {
      title: "Reallocation Ready",
      desc: status === "REALLOCATED" ? "Reallocated" : eligibility === "ELIGIBLE" ? "Eligible" : "Pending",
      completed: status === "REALLOCATED" || eligibility === "ELIGIBLE",
      current: eligibility === "ELIGIBLE",
    },
  ];

  return (
    <div className="w-full py-4">
      <div className="relative flex items-center justify-between">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 w-full bg-slate-800 -z-0" />

        {steps.map((s, idx) => (
          <div key={idx} className="relative z-10 flex flex-col items-center text-center px-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center border text-xs font-bold transition-all ${
                s.completed
                  ? "bg-emerald-950 border-emerald-500 text-emerald-400"
                  : s.current
                  ? "bg-amber-950 border-amber-500 text-amber-300 animate-pulse"
                  : "bg-slate-900 border-slate-700 text-slate-500"
              }`}
            >
              {s.completed ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <span>{idx + 1}</span>
              )}
            </div>

            <div className="mt-2 text-xs font-semibold text-slate-200">{s.title}</div>
            <div className="text-[10px] text-slate-400 max-w-[90px]">{s.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
