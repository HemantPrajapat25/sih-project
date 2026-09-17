"use client";

import React from "react";
import { useAuth } from "@/lib/auth-context";
import { Permission } from "@/types";
import { Lock } from "lucide-react";

interface RoleGuardProps {
  permission: Permission;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function RoleGuard({ permission, children, fallback }: RoleGuardProps) {
  const { hasPermission } = useAuth();

  if (!hasPermission(permission)) {
    if (fallback) return <>{fallback}</>;
    return (
      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
        <Lock className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
        <span>Action restricted. Privilege &apos;{permission}&apos; required.</span>
      </div>
    );
  }

  return <>{children}</>;
}
