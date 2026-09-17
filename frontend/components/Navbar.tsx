"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldCheck, ChevronDown, LogOut, KeyRound, Building2,
  Cpu, Users2, BarChart3, ClipboardList,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Role, OrganizationType } from "@/types";

const ALL_ROLES: Array<{ role: Role; label: string; org: string; orgType: string }> = [
  { role: "SUPER_ADMIN",              label: "Super Admin",        org: "NumberGuard Platform",    orgType: "PLATFORM" },
  { role: "TELECOM_ADMIN",            label: "Telecom Admin",      org: "DemoTel Telecom",         orgType: "TELECOM" },
  { role: "TELECOM_OPERATOR",         label: "Telecom Operator",   org: "DemoTel Telecom",         orgType: "TELECOM" },
  { role: "SERVICE_PROVIDER_ADMIN",   label: "Bank Lead Admin",    org: "SecureBank Ltd",          orgType: "BANK" },
  { role: "SERVICE_PROVIDER_OPERATOR",label: "SecOps Operator",    org: "SecureBank Ltd",          orgType: "BANK" },
  { role: "AUDITOR",                  label: "External Auditor",   org: "Deloitte Compliance",     orgType: "AUDITOR" },
  { role: "ANALYST",                  label: "Risk Analyst",       org: "NumberGuard Analytics",   orgType: "PLATFORM" },
];

const ORG_TYPE_BADGE: Record<string, { label: string; cls: string }> = {
  PLATFORM:             { label: "Platform",  cls: "bg-purple-950 text-purple-400 border-purple-800/60" },
  TELECOM:              { label: "Telecom",   cls: "bg-cyan-950 text-cyan-400 border-cyan-800/60" },
  BANK:                 { label: "Bank",      cls: "bg-amber-950 text-amber-400 border-amber-800/60" },
  FINTECH:              { label: "Fintech",   cls: "bg-amber-950 text-amber-400 border-amber-800/60" },
  ECOMMERCE:            { label: "E-Commerce",cls: "bg-orange-950 text-orange-400 border-orange-800/60" },
  MOBILITY:             { label: "Mobility",  cls: "bg-blue-950 text-blue-400 border-blue-800/60" },
  OTHER_SERVICE_PROVIDER:{ label: "Partner", cls: "bg-slate-800 text-slate-300 border-slate-700" },
  AUDITOR_ORGANIZATION: { label: "Auditor",  cls: "bg-rose-950 text-rose-400 border-rose-800/60" },
};

const ROLE_ICON: Record<Role, React.ElementType> = {
  SUPER_ADMIN:              Cpu,
  TELECOM_ADMIN:            Building2,
  TELECOM_OPERATOR:         Building2,
  SERVICE_PROVIDER_ADMIN:   Users2,
  SERVICE_PROVIDER_OPERATOR:Users2,
  ANALYST:                  BarChart3,
  AUDITOR:                  ClipboardList,
};

export function Navbar() {
  const router = useRouter();
  const { user, role, switchDemoRole, logout, getDashboard } = useAuth();
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);

  const orgType = (user?.organization_type as string) || "TELECOM";
  const badge = ORG_TYPE_BADGE[orgType] || ORG_TYPE_BADGE["TELECOM"];
  const RoleIcon = ROLE_ICON[role] || Building2;

  async function handleRoleSwitch(targetRole: Role) {
    setRoleDropdownOpen(false);
    await switchDemoRole(targetRole);
    // Navigate to new role's dashboard after switch
    const { getDashboardPath } = await import("@/types");
    router.push(getDashboardPath(targetRole));
  }

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
      {/* Brand */}
      <Link href={getDashboard()} className="flex items-center gap-2.5 group flex-shrink-0">
        <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:border-cyan-400/60 transition-colors">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-tight text-white text-base">
              Number<span className="text-cyan-400">Guard</span>
            </span>
            <span className={`text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded border ${badge.cls}`}>
              {badge.label}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-none mt-0.5 hidden md:block">
            {user?.organization_name || "Telecom Lifecycle Platform"}
          </p>
        </div>
      </Link>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Live indicator */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/40 text-[11px] text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Stream: Live</span>
        </div>

        {/* DEMO Role Switcher */}
        <div className="relative">
          <button
            onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-200 transition-all cursor-pointer"
            title="Switch demo role to preview RBAC permissions"
          >
            <KeyRound className="w-3.5 h-3.5 text-cyan-400" />
            <div className="text-left hidden sm:block">
              <div className="text-[10px] text-slate-400 leading-tight">DEMO Role</div>
              <div className="text-cyan-300 font-semibold text-[11px]">{role.replace(/_/g, " ")}</div>
            </div>
            <ChevronDown className="w-3 h-3 text-slate-400 ml-1" />
          </button>

          {roleDropdownOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-2 z-50">
              <div className="px-2 py-1.5 border-b border-slate-800 mb-1.5">
                <p className="text-[11px] font-semibold text-slate-300">Switch RBAC Persona</p>
                <p className="text-[10px] text-slate-500">Preview system under different roles & portals</p>
              </div>
              <div className="space-y-0.5 max-h-72 overflow-y-auto">
                {ALL_ROLES.map((r) => {
                  const b = ORG_TYPE_BADGE[r.orgType] || ORG_TYPE_BADGE["TELECOM"];
                  return (
                    <button
                      key={r.role}
                      onClick={() => handleRoleSwitch(r.role)}
                      className={`w-full text-left px-2.5 py-2 rounded-lg text-xs flex items-center justify-between transition-colors cursor-pointer ${
                        role === r.role
                          ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30"
                          : "text-slate-300 hover:bg-slate-800"
                      }`}
                    >
                      <div>
                        <div className="font-semibold flex items-center gap-1.5">
                          <span>{r.label}</span>
                          {role === r.role && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 inline-block" />}
                        </div>
                        <div className="text-[10px] text-slate-400">{r.org}</div>
                      </div>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${b.cls}`}>
                        {b.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* User card */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 font-bold text-xs flex-shrink-0">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-slate-200 truncate max-w-[140px]">
              {user?.full_name?.split(" ").slice(0, 2).join(" ") || "Operator"}
            </div>
            <div className="text-[10px] text-slate-400 truncate max-w-[140px]">
              {user?.organization_name || "Carrier Tenant"}
            </div>
          </div>
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="p-2 rounded-lg hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
