import React from "react";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: "cyan" | "emerald" | "amber" | "rose" | "purple";
  badge?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = "cyan",
  badge,
}: MetricCardProps) {
  const colorMap = {
    cyan: {
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/20",
      icon: "text-cyan-400",
      badge: "bg-cyan-950/80 text-cyan-400 border-cyan-800/40",
    },
    emerald: {
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
      icon: "text-emerald-400",
      badge: "bg-emerald-950/80 text-emerald-400 border-emerald-800/40",
    },
    amber: {
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      icon: "text-amber-400",
      badge: "bg-amber-950/80 text-amber-400 border-amber-800/40",
    },
    rose: {
      bg: "bg-rose-500/10",
      border: "border-rose-500/20",
      icon: "text-rose-400",
      badge: "bg-rose-950/80 text-rose-400 border-rose-800/40",
    },
    purple: {
      bg: "bg-purple-500/10",
      border: "border-purple-500/20",
      icon: "text-purple-400",
      badge: "bg-purple-950/80 text-purple-400 border-purple-800/40",
    },
  };

  const scheme = colorMap[color];

  return (
    <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all">
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-slate-400">{title}</span>
        <div className={`p-2 rounded-lg ${scheme.bg} ${scheme.border} border`}>
          <Icon className={`w-4 h-4 ${scheme.icon}`} />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
        {badge && (
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${scheme.badge}`}>
            {badge}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-1 text-[11px] text-slate-400">{subtitle}</p>}
    </div>
  );
}
