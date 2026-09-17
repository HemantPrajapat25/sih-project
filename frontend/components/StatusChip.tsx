import React from "react";

interface StatusChipProps {
  status: string;
  size?: "sm" | "md";
}

export function StatusChip({ status, size = "md" }: StatusChipProps) {
  const normalized = status.toUpperCase();

  let styles = "bg-slate-800 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";
  let label = status;

  switch (normalized) {
    case "DECOMMISSIONED":
      styles = "bg-blue-950/70 text-blue-300 border-blue-800/60";
      dotColor = "bg-blue-400";
      label = "Decommissioned";
      break;
    case "NOTIFYING_PROVIDERS":
      styles = "bg-purple-950/70 text-purple-300 border-purple-800/60";
      dotColor = "bg-purple-400 animate-pulse";
      label = "Notifying Providers";
      break;
    case "COOLING_HOLD":
      styles = "bg-amber-950/70 text-amber-300 border-amber-800/60";
      dotColor = "bg-amber-400";
      label = "Cooling Hold";
      break;
    case "MANUAL_REVIEW":
    case "MANUAL_REVIEW_REQUIRED":
      styles = "bg-rose-950/70 text-rose-300 border-rose-800/60";
      dotColor = "bg-rose-400";
      label = "Manual Review";
      break;
    case "BLOCKED":
      styles = "bg-red-950/80 text-red-300 border-red-800/80";
      dotColor = "bg-red-400";
      label = "Blocked";
      break;
    case "ELIGIBLE":
    case "ELIGIBLE_FOR_REALLOCATION":
      styles = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
      dotColor = "bg-emerald-400";
      label = "Eligible";
      break;
    case "REALLOCATED":
      styles = "bg-slate-800/70 text-slate-300 border-slate-700";
      dotColor = "bg-slate-400";
      label = "Reallocated";
      break;
    case "SENT":
      styles = "bg-cyan-950/70 text-cyan-300 border-cyan-800/60";
      dotColor = "bg-cyan-400";
      label = "Sent";
      break;
    case "ACKNOWLEDGED":
      styles = "bg-indigo-950/70 text-indigo-300 border-indigo-800/60";
      dotColor = "bg-indigo-400";
      label = "Acknowledged";
      break;
    case "REMEDIATED":
      styles = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
      dotColor = "bg-emerald-400";
      label = "Remediated";
      break;
    case "FAILED":
      styles = "bg-rose-950/70 text-rose-300 border-rose-800/60";
      dotColor = "bg-rose-400";
      label = "Failed";
      break;
  }

  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";

  return (
    <span className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${styles} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{label}</span>
    </span>
  );
}
