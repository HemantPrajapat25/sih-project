"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Hash, Clock, Flame, Building2, BellRing, Snowflake,
  CheckCircle2, FileText, BarChart3, Cpu, Users2, Settings, ShieldCheck,
  Key, Briefcase, ListTodo, FolderOpen, TrendingUp, Globe, AlertOctagon,
  ClipboardList, Network,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Role } from "@/types";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: "cyan" | "emerald" | "amber" | "rose" | "purple";
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const NAV_BY_ROLE: Record<Role, NavSection[]> = {
  SUPER_ADMIN: [
    {
      label: "Platform Command",
      items: [
        { name: "Platform Dashboard", href: "/platform/dashboard", icon: LayoutDashboard, badge: "HQ", badgeColor: "purple" },
        { name: "Organizations", href: "/platform/organizations", icon: Globe },
      ],
    },
    {
      label: "Oversight",
      items: [
        { name: "Risk Engine", href: "/risk", icon: Flame },
        { name: "Audit Trail", href: "/audit", icon: FileText },
        { name: "Analytics", href: "/analytics", icon: BarChart3 },
      ],
    },
    {
      label: "Administration",
      items: [
        { name: "Users & Roles", href: "/users", icon: Users2 },
        { name: "API & Integrations", href: "/integrations", icon: Cpu },
        { name: "API Keys", href: "/settings/api-keys", icon: Key },
        { name: "Platform Settings", href: "/settings", icon: Settings },
      ],
    },
  ],

  TELECOM_ADMIN: [
    {
      label: "Lifecycle Command",
      items: [
        { name: "Telecom Dashboard", href: "/telecom/dashboard", icon: LayoutDashboard, badge: "Admin" },
        { name: "Numbers Inventory", href: "/numbers", icon: Hash },
        { name: "Decommissioning Queue", href: "/queue", icon: Clock },
      ],
    },
    {
      label: "Risk & Compliance",
      items: [
        { name: "Risk Engine", href: "/risk", icon: Flame, badge: "Live", badgeColor: "rose" },
        { name: "Cooling Periods", href: "/cooling", icon: Snowflake },
        { name: "Allocation Readiness", href: "/readiness", icon: CheckCircle2, badge: "Eligible", badgeColor: "emerald" },
      ],
    },
    {
      label: "Partners & Monitoring",
      items: [
        { name: "Service Providers", href: "/providers", icon: Building2 },
        { name: "Notifications", href: "/notifications", icon: BellRing },
        { name: "Audit Trail", href: "/audit", icon: FileText },
        { name: "Analytics", href: "/analytics", icon: BarChart3 },
      ],
    },
    {
      label: "Administration",
      items: [
        { name: "API & Integrations", href: "/integrations", icon: Cpu },
        { name: "Users & Roles", href: "/users", icon: Users2 },
        { name: "Organization Settings", href: "/settings", icon: Settings },
      ],
    },
  ],

  TELECOM_OPERATOR: [
    {
      label: "Operations",
      items: [
        { name: "Operations Workspace", href: "/telecom/operations", icon: LayoutDashboard },
        { name: "Numbers Inventory", href: "/numbers", icon: Hash },
        { name: "Decommissioning Queue", href: "/queue", icon: Clock, badge: "Tasks", badgeColor: "amber" },
      ],
    },
    {
      label: "Monitoring",
      items: [
        { name: "Risk View", href: "/risk", icon: Flame },
        { name: "Notifications", href: "/notifications", icon: BellRing },
        { name: "Cooling Periods", href: "/cooling", icon: Snowflake },
        { name: "Audit Trail", href: "/audit", icon: FileText },
      ],
    },
  ],

  SERVICE_PROVIDER_ADMIN: [
    {
      label: "Provider Portal",
      items: [
        { name: "Provider Dashboard", href: "/provider/dashboard", icon: LayoutDashboard, badge: "Admin" },
        { name: "Active Cases", href: "/provider/cases", icon: FolderOpen, badge: "Action", badgeColor: "amber" },
        { name: "Task Queue", href: "/provider/tasks", icon: ListTodo },
      ],
    },
    {
      label: "Management",
      items: [
        { name: "Notifications", href: "/notifications", icon: BellRing },
        { name: "Audit Trail", href: "/audit", icon: FileText },
        { name: "API Keys", href: "/settings/api-keys", icon: Key },
        { name: "Provider Settings", href: "/settings", icon: Settings },
      ],
    },
  ],

  SERVICE_PROVIDER_OPERATOR: [
    {
      label: "My Work",
      items: [
        { name: "Task Queue", href: "/provider/tasks", icon: ListTodo, badge: "Assigned", badgeColor: "cyan" },
        { name: "Cases", href: "/provider/cases", icon: FolderOpen },
      ],
    },
    {
      label: "Reference",
      items: [
        { name: "Notifications", href: "/notifications", icon: BellRing },
        { name: "Audit Trail", href: "/audit", icon: FileText },
      ],
    },
  ],

  ANALYST: [
    {
      label: "Analytics Portal",
      items: [
        { name: "Analytics Dashboard", href: "/analytics/dashboard", icon: TrendingUp, badge: "Analyst" },
        { name: "Risk Engine", href: "/risk", icon: Flame },
      ],
    },
    {
      label: "Data Access",
      items: [
        { name: "Numbers (Read-only)", href: "/numbers", icon: Hash },
        { name: "Audit Trail", href: "/audit", icon: FileText },
        { name: "Analytics", href: "/analytics", icon: BarChart3 },
      ],
    },
  ],

  AUDITOR: [
    {
      label: "Compliance Portal",
      items: [
        { name: "Audit Dashboard", href: "/audit/dashboard", icon: ClipboardList, badge: "Auditor" },
        { name: "Full Audit Trail", href: "/audit", icon: FileText },
        { name: "Risk View", href: "/risk", icon: AlertOctagon },
      ],
    },
    {
      label: "Read-only Access",
      items: [
        { name: "Numbers (View)", href: "/numbers", icon: Hash },
        { name: "Cooling Periods", href: "/cooling", icon: Snowflake },
      ],
    },
  ],
};

const BADGE_COLORS: Record<string, string> = {
  cyan:    "bg-cyan-950/80 text-cyan-400 border border-cyan-800/50",
  emerald: "bg-emerald-950/80 text-emerald-400 border border-emerald-800/50",
  amber:   "bg-amber-950/80 text-amber-400 border border-amber-800/50",
  rose:    "bg-rose-950/80 text-rose-400 border border-rose-800/50",
  purple:  "bg-purple-950/80 text-purple-400 border border-purple-800/50",
};

const ORG_TYPE_FOOTER: Record<Role, { label: string; color: string }> = {
  SUPER_ADMIN:              { label: "Platform Authority", color: "text-purple-400" },
  TELECOM_ADMIN:            { label: "Telecom Lifecycle Admin", color: "text-cyan-400" },
  TELECOM_OPERATOR:         { label: "Carrier Operations", color: "text-cyan-400" },
  SERVICE_PROVIDER_ADMIN:   { label: "Partner Organisation Admin", color: "text-amber-400" },
  SERVICE_PROVIDER_OPERATOR:{ label: "Partner Remediation Ops", color: "text-amber-400" },
  ANALYST:                  { label: "Analytics & Risk Bureau", color: "text-emerald-400" },
  AUDITOR:                  { label: "Compliance & Audit Body", color: "text-rose-400" },
};

export function Sidebar() {
  const pathname = usePathname();
  const { role } = useAuth();
  const sections = NAV_BY_ROLE[role] || NAV_BY_ROLE.TELECOM_ADMIN;
  const footer = ORG_TYPE_FOOTER[role];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950/40 backdrop-blur-md flex flex-col flex-shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-3 flex-1 space-y-4 overflow-y-auto">
        {sections.map((section) => (
          <div key={section.label}>
            <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider font-semibold text-slate-500">
              {section.label}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && item.href.length > 1 && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                      isActive
                        ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon
                        className={`w-4 h-4 flex-shrink-0 transition-colors ${
                          isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                        }`}
                      />
                      <span className="truncate">{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${BADGE_COLORS[item.badgeColor || "cyan"]}`}>
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Role context footer */}
      <div className="p-4 border-t border-slate-800/80">
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] space-y-1.5">
          <div className={`flex items-center gap-1.5 font-semibold ${footer.color}`}>
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{footer.label}</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            Subscriber personal identities and records are never collected, exposed, or stored.
          </p>
        </div>
      </div>
    </aside>
  );
}
