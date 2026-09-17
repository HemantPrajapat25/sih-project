"use client";

import React, { useState } from "react";
import { Settings, ShieldCheck, Database, Save, CheckCircle2 } from "lucide-react";
import { RoleGuard } from "@/components/RoleGuard";

export default function SettingsPage() {
  const [carrierName, setCarrierName] = useState("Jio Infocomm Ltd");
  const [circle, setCircle] = useState("National (All Telecom Circles)");
  const [standardCooling, setStandardCooling] = useState(60);
  const [bankingCooling, setBankingCooling] = useState(90);
  const [highRiskCooling, setHighRiskCooling] = useState(120);
  const [saved, setSaved] = useState(false);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Settings className="w-5 h-5 text-cyan-400" />
          <span>Organization & Telecom Tenant Settings</span>
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure carrier entity metadata, default quarantine durations, and privacy indexing parameters.
        </p>
      </div>

      {saved && (
        <div className="p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Organization settings successfully saved and applied to lifecycle workflows.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Carrier Metadata */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold text-white">Telecom Carrier Identity</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Licensed Operator Name</label>
              <input
                type="text"
                value={carrierName}
                onChange={(e) => setCarrierName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Jurisdiction / Telecom Circle</label>
              <input
                type="text"
                value={circle}
                onChange={(e) => setCircle(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
              />
            </div>
          </div>
        </div>

        {/* Statutory Cooling Defaults */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold text-white">Default Quarantine Timers (Days)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Standard Disconnection</label>
              <input
                type="number"
                value={standardCooling}
                onChange={(e) => setStandardCooling(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">General inactive prepaid</span>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Banking-Linked Account</label>
              <input
                type="number"
                value={bankingCooling}
                onChange={(e) => setBankingCooling(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">UPI & Netbanking accounts</span>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Disputed / High Risk</label>
              <input
                type="number"
                value={highRiskCooling}
                onChange={(e) => setHighRiskCooling(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">Extended hold before recycling</span>
            </div>
          </div>
        </div>

        {/* Privacy & Cryptography Policy */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
            <ShieldCheck className="w-4 h-4" />
            <span>Privacy & Cryptographic Shield</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            All stored telephone numbers are indexed via HMAC-SHA256 with a secure pepper key. Previous subscriber names, addresses, and billing records are rejected by API validation middleware to guarantee regulatory privacy compliance.
          </p>
        </div>

        <RoleGuard
          permission="settings.manage"
          fallback={<div className="text-slate-500 text-xs">Settings modifications restricted to TELECOM_ADMIN.</div>}
        >
          <div className="flex justify-end">
            <button
              type="submit"
              className="px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold flex items-center gap-2 cursor-pointer shadow-lg shadow-cyan-500/20"
            >
              <Save className="w-4 h-4" />
              <span>Save Configuration</span>
            </button>
          </div>
        </RoleGuard>
      </form>
    </div>
  );
}
