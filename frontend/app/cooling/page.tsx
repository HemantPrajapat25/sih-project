"use client";

import React, { useState, useEffect } from "react";
import { Snowflake, Clock, ShieldAlert, CheckCircle2, Sliders, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { CoolingRule } from "@/types";

export default function CoolingPeriodsPage() {
  const [rules, setRules] = useState<CoolingRule[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      const data = await api.getCoolingRules();
      setRules(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Snowflake className="w-5 h-5 text-cyan-400" />
            <span>Cooling Period & Quarantine Policy Engine</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Configurable statutory quarantine rules by carrier, subscriber risk category, and banking associations.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white self-start"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-3 py-12 text-center text-slate-500 text-xs">
            Loading cooling period policies...
          </div>
        ) : (
          rules.map((r) => (
            <div
              key={r.id}
              className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between space-y-6"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                    {r.carrier === "ALL" ? "National Standard" : r.carrier}
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Active Policy</span>
                  </span>
                </div>

                <h2 className="text-base font-bold text-white mt-2">{r.name}</h2>
                <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Minimum Quarantine:</span>
                    <span className="font-bold text-cyan-400">{r.min_cooling_days} Days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Risk Extension Hold:</span>
                    <span className="font-bold text-amber-400">+{r.risk_extension_days} Days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Auto-Extend on Overdue:</span>
                    <span className="font-semibold text-slate-200">
                      {r.auto_extend_on_overdue ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                </div>

                <div className="mt-4 text-xs">
                  <span className="font-medium text-slate-400">Mandatory Release Condition:</span>
                  <p className="mt-1 text-slate-300 bg-slate-900/90 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed text-[11px]">
                    {r.release_condition}
                  </p>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500">
                Created: {new Date(r.created_at).toLocaleDateString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
