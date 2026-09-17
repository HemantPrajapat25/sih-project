import React from "react";

interface RiskBadgeProps {
  score?: number;
  level?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  showScore?: boolean;
}

export function RiskBadge({ score, level, showScore = true }: RiskBadgeProps) {
  const computedScore = score !== undefined ? score : (level === "LOW" ? 15 : level === "MEDIUM" ? 40 : level === "HIGH" ? 65 : 90);
  const computedLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" = level || (
    computedScore <= 25 ? "LOW" : computedScore <= 55 ? "MEDIUM" : computedScore <= 79 ? "HIGH" : "CRITICAL"
  );

  let color = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
  let barColor = "bg-emerald-400";

  switch (computedLevel) {
    case "LOW":
      color = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
      barColor = "bg-emerald-400";
      break;
    case "MEDIUM":
      color = "bg-amber-950/70 text-amber-300 border-amber-800/60";
      barColor = "bg-amber-400";
      break;
    case "HIGH":
      color = "bg-orange-950/70 text-orange-300 border-orange-800/60";
      barColor = "bg-orange-400";
      break;
    case "CRITICAL":
      color = "bg-rose-950/80 text-rose-300 border-rose-800/80";
      barColor = "bg-rose-400";
      break;
  }

  return (
    <div className="inline-flex items-center gap-2">
      <span className={`px-2 py-0.5 rounded-md text-[11px] font-semibold border ${color}`}>
        {score !== undefined && showScore ? `${computedScore}/100 • ${computedLevel}` : computedLevel}
      </span>
    </div>
  );
}
