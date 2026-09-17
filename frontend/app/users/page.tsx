"use client";

import React, { useState, useEffect } from "react";
import { Users2, ShieldCheck, KeyRound, Check, X, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { User, Role } from "@/types";

const ALL_ROLES: Role[] = [
  "SUPER_ADMIN",
  "TELECOM_ADMIN",
  "TELECOM_OPERATOR",
  "SERVICE_PROVIDER_ADMIN",
  "SERVICE_PROVIDER_OPERATOR",
  "AUDITOR",
  "ANALYST",
];

export default function UsersAndRolesPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [matrix, setMatrix] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      const [uList, rbac] = await Promise.all([api.getUsers(), api.getRbacMatrix()]);
      setUsers(uList);
      setMatrix(rbac);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const allPermissions = [
    "numbers.read",
    "numbers.import",
    "numbers.update",
    "numbers.reallocate",
    "risk.read",
    "risk.override",
    "providers.manage",
    "notifications.send",
    "notifications.acknowledge",
    "audit.read",
    "integrations.manage",
    "users.manage",
    "settings.manage",
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Users2 className="w-5 h-5 text-cyan-400" />
            <span>Users & Role-Based Access Control (RBAC)</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Strict role permissions matrix enforced at both API dependency and frontend UI layers.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white self-start"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Users Table */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Active Operator & Partner Accounts
        </h2>
        <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4">User Name</th>
                <th className="py-3 px-3">Email</th>
                <th className="py-3 px-3">Role</th>
                <th className="py-3 px-3">Organization</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/40">
                  <td className="py-3 px-4 font-semibold text-slate-200">{u.full_name}</td>
                  <td className="py-3 px-3 font-mono text-slate-300">{u.email}</td>
                  <td className="py-3 px-3">
                    <span className="font-semibold text-cyan-300 px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-800/60">
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-400">{u.organization_name || "Platform"}</td>
                  <td className="py-3 px-3">
                    <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-800/60">
                      Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* RBAC Granular Matrix Table */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Granular RBAC Privilege Matrix
        </h2>
        <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-x-auto shadow-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4 min-w-[200px]">Permission</th>
                {ALL_ROLES.map((r) => (
                  <th key={r} className="py-3 px-2 text-center min-w-[90px] font-semibold text-[10px]">
                    {r.replace("_", " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {allPermissions.map((perm) => (
                <tr key={perm} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-4 font-mono font-medium text-slate-300">{perm}</td>
                  {ALL_ROLES.map((r) => {
                    const has = matrix[r]?.includes(perm);
                    return (
                      <td key={r} className="py-2.5 px-2 text-center">
                        {has ? (
                          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                            <Check className="w-3 h-3" />
                          </span>
                        ) : (
                          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-slate-600">
                            <X className="w-3 h-3" />
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
