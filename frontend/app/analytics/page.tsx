"use client";

import React, { useState, useEffect } from "react";
import { BarChart3, TrendingUp, ShieldCheck, Activity, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { DashboardKPIs } from "@/types";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<DashboardKPIs | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      const data = await api.getDashboardMetrics();
      setMetrics(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const slaData = [
    { provider: "HDFC", avgHours: 12.4, compliance: 98 },
    { provider: "SBI", avgHours: 18.2, compliance: 94 },
    { provider: "Paytm", avgHours: 6.1, compliance: 99 },
    { provider: "PhonePe", avgHours: 7.5, compliance: 99 },
    { provider: "Amazon", avgHours: 23.8, compliance: 91 },
    { provider: "Flipkart", avgHours: 22.0, compliance: 92 },
    { provider: "WhatsApp", avgHours: 11.5, compliance: 97 },
    { provider: "Google", avgHours: 13.9, compliance: 96 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Telecom Reallocation Analytics & KPIs</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Deep-dive metrics on quarantine throughput, provider unlinking response rates, and residual identity collision probability.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white self-start"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Chart 1: Lifecycle Volume Velocity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
          <div>
            <h2 className="text-sm font-bold text-white">Quarantine Intake vs Release Velocity</h2>
            <p className="text-xs text-slate-400">Monthly volume of decommissioned vs cleared mobile numbers</p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics?.lifecycle_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Line type="monotone" dataKey="decommissioned" name="Decommissioned" stroke="#06b6d4" strokeWidth={2} />
                <Line type="monotone" dataKey="reallocated" name="Reallocated" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Provider Response SLA Performance */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
          <div>
            <h2 className="text-sm font-bold text-white">Digital Provider Response SLA (Hours)</h2>
            <p className="text-xs text-slate-400">Average time taken by banks & platforms to unlink accounts</p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={slaData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="provider" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="avgHours" name="Avg SLA (Hours)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
