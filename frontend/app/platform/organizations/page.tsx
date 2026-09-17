"use client";

import React, { useState } from "react";
import {
  Globe, Building2, Plus, Search, Filter, CheckCircle2,
  Users2, Hash, ChevronRight, Cpu, X,
} from "lucide-react";

const ORG_DATA = [
  { id: "org-1", name: "DemoTel Telecom", type: "TELECOM", status: "ACTIVE", email: "admin@demotel.demo", numbers: 1480, users: 12, modules: ["lifecycle","risk","audit"] },
  { id: "org-2", name: "SecureBank Ltd", type: "BANK", status: "ACTIVE", email: "admin@securebank.demo", numbers: 0, users: 5, modules: ["provider_portal","notifications"] },
  { id: "org-3", name: "PayFlow Fintech", type: "FINTECH", status: "ACTIVE", email: "admin@payflow.demo", numbers: 0, users: 3, modules: ["provider_portal","notifications"] },
  { id: "org-4", name: "ShopKart E-Commerce", type: "ECOMMERCE", status: "ACTIVE", email: "admin@shopkart.demo", numbers: 0, users: 4, modules: ["provider_portal"] },
  { id: "org-5", name: "Deloitte Compliance", type: "AUDITOR_ORGANIZATION", status: "ACTIVE", email: "auditor@deloitte.demo", numbers: 0, users: 2, modules: ["audit"] },
  { id: "org-6", name: "RegAnalytics Bureau", type: "PLATFORM", status: "ACTIVE", email: "analyst@numberguard.demo", numbers: 0, users: 1, modules: ["analytics","risk"] },
];

const TYPE_BADGE: Record<string, { label: string; cls: string }> = {
  TELECOM:              { label: "Telecom",  cls: "bg-cyan-950 text-cyan-400 border-cyan-800/60" },
  BANK:                 { label: "Bank",     cls: "bg-amber-950 text-amber-400 border-amber-800/60" },
  FINTECH:              { label: "Fintech",  cls: "bg-amber-950 text-amber-400 border-amber-800/60" },
  ECOMMERCE:            { label: "E-Com",    cls: "bg-orange-950 text-orange-400 border-orange-800/60" },
  AUDITOR_ORGANIZATION: { label: "Auditor",  cls: "bg-rose-950 text-rose-400 border-rose-800/60" },
  PLATFORM:             { label: "Platform", cls: "bg-purple-950 text-purple-400 border-purple-800/60" },
};

export default function PlatformOrganizationsPage() {
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);

  const filtered = ORG_DATA.filter(
    (o) => o.name.toLowerCase().includes(search.toLowerCase()) || o.type.includes(search.toUpperCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest font-semibold text-purple-400 px-2 py-0.5 rounded-full bg-purple-950 border border-purple-800/60">Super Admin</span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-purple-400" /> Organisation Registry
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">Provision, inspect, and manage all tenant organisations on NumberGuard.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-md shadow-purple-500/20">
          <Plus className="w-3.5 h-3.5" /> Provision Organisation
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Orgs", value: ORG_DATA.length, icon: Globe, color: "purple" },
          { label: "Telecom Orgs", value: ORG_DATA.filter(o => o.type === "TELECOM").length, icon: Building2, color: "cyan" },
          { label: "Partner Orgs", value: ORG_DATA.filter(o => ["BANK","FINTECH","ECOMMERCE"].includes(o.type)).length, icon: Users2, color: "amber" },
          { label: "Numbers Managed", value: ORG_DATA.reduce((s, o) => s + o.numbers, 0).toLocaleString(), icon: Hash, color: "emerald" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
            <div className={`p-2.5 rounded-lg border ${
              color === "purple" ? "bg-purple-500/10 border-purple-500/20 text-purple-400" :
              color === "cyan"   ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-400" :
              color === "amber"  ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                                   "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
            }`}>
              <Icon className="w-4 h-4" />
            </div>
            <div>
              <div className="text-lg font-bold text-white">{value}</div>
              <div className="text-[11px] text-slate-400">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search organisations…"
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-purple-500 placeholder-slate-600"
          />
        </div>
        <button className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors">
          <Filter className="w-4 h-4" />
        </button>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-500">
              {["Organisation", "Type", "Contact Email", "Numbers", "Users", "Modules", "Status", ""].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.map((org) => {
              const b = TYPE_BADGE[org.type] || TYPE_BADGE.PLATFORM;
              return (
                <tr key={org.id} className="hover:bg-slate-800/30 transition-colors group">
                  <td className="px-4 py-3 font-semibold text-slate-200">{org.name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${b.cls}`}>{b.label}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{org.email}</td>
                  <td className="px-4 py-3 text-slate-300">{org.numbers.toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-300">{org.users}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {org.modules.map(m => (
                        <span key={m} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px]">{m}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1.5 text-emerald-400"><CheckCircle2 className="w-3.5 h-3.5" />{org.status}</span>
                  </td>
                  <td className="px-4 py-3">
                    <button className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white transition-all">
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Provision Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Provision New Organisation</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>
            <div className="space-y-3 text-xs">
              {[
                { label: "Organisation Name", placeholder: "e.g. Airtel Telecom" },
                { label: "Contact Email", placeholder: "admin@org.example" },
                { label: "Primary Domain", placeholder: "org.example" },
              ].map(f => (
                <div key={f.label}>
                  <label className="block text-slate-300 font-medium mb-1">{f.label}</label>
                  <input placeholder={f.placeholder} className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-purple-500 placeholder-slate-600 text-xs" />
                </div>
              ))}
              <div>
                <label className="block text-slate-300 font-medium mb-1">Organisation Type</label>
                <select className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-purple-500 text-xs">
                  {["TELECOM","BANK","FINTECH","ECOMMERCE","MOBILITY","AUDITOR_ORGANIZATION"].map(t => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <button onClick={() => setShowModal(false)} className="flex-1 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700 transition-colors">Cancel</button>
              <button onClick={() => { alert("Organisation provisioned (demo)"); setShowModal(false); }}
                className="flex-1 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> Provision
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
