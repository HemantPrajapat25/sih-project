"use client";

import React, { useState, useEffect } from "react";
import { Building2, Activity, Wifi, Clock, AlertCircle, RefreshCw, CheckCircle2, Play } from "lucide-react";
import { api } from "@/lib/api";
import { ServiceProvider } from "@/types";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ServiceProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [pingResult, setPingResult] = useState<{ id: string; latency: number } | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const data = await api.getProviders();
      setProviders(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handlePing(id: string) {
    try {
      const res = await api.pingProvider(id);
      setPingResult({ id, latency: res.latency_ms || 42 });
      setTimeout(() => setPingResult(null), 3000);
    } catch (err: any) {
      alert("Ping failed: " + err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Building2 className="w-5 h-5 text-purple-400" />
            <span>Digital Service Provider Directory</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Registered banks, fintechs, identity providers, and platforms receiving privacy-preserving unlinking notifications.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white self-start"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Grid of Providers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3 py-12 text-center text-slate-500 text-xs">
            Loading service provider directory...
          </div>
        ) : (
          providers.map((p) => {
            const isPinged = pingResult?.id === p.id;
            return (
              <div
                key={p.id}
                className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-sm font-bold text-white">{p.name}</h2>
                      <span className="text-[10px] uppercase font-semibold text-cyan-400">
                        Code: {p.code} • {p.category}
                      </span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 border border-emerald-800/60 text-emerald-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>{p.status}</span>
                    </span>
                  </div>

                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex items-center justify-between text-slate-400">
                      <span>Integration Protocol:</span>
                      <span className="font-mono text-slate-200">{p.integration_type}</span>
                    </div>

                    <div className="flex items-center justify-between text-slate-400">
                      <span>Remediation SLA:</span>
                      <span className="font-medium text-slate-200">{p.avg_sla_hours} hrs</span>
                    </div>

                    <div className="flex items-center justify-between text-slate-400">
                      <span>Unresolved Alerts:</span>
                      <span className={`font-semibold ${p.unresolved_count > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                        {p.unresolved_count}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-slate-400">
                      <span>Total Dispatched:</span>
                      <span className="font-medium text-slate-200">{p.notification_count}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <span className="text-[10px] text-slate-500">
                    Sync: {new Date(p.last_sync_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>

                  <button
                    onClick={() => handlePing(p.id)}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    {isPinged ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">{pingResult?.latency}ms (OK)</span>
                      </>
                    ) : (
                      <>
                        <Wifi className="w-3.5 h-3.5" />
                        <span>Test Ping</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
