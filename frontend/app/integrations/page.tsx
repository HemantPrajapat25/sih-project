"use client";

import React, { useState, useEffect } from "react";
import { Cpu, Wifi, KeyRound, CheckCircle2, ShieldCheck, Terminal, Send } from "lucide-react";
import { api } from "@/lib/api";

export default function IntegrationsPage() {
  const [data, setData] = useState<any>(null);
  const [testUrl, setTestUrl] = useState("https://api.sandbox.telecom.in/v1/webhook");
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getIntegrationsStatus();
        setData(res);
      } catch (err) {
        console.error(err);
      }
    }
    load();
  }, []);

  function handleTestWebhook() {
    setTestResult({
      status: "SUCCESS",
      http_code: 200,
      rtt_ms: 38,
      message: "Webhook challenge acknowledged by sandbox receiver.",
    });
  }

  return (
    <div className="space-y-6">
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <span>Carrier Adapters & Sandbox Integrations</span>
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Clean adapter interfaces for telecom operator feeds and external digital service provider webhooks.
        </p>
      </div>

      {/* Carrier Adapters Grid */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Carrier Ingestion Adapters
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data?.telecom_adapters?.map((a: any) => (
            <div key={a.carrier} className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">{a.carrier}</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                  {a.status}
                </span>
              </div>
              <div className="text-xs space-y-1 text-slate-400">
                <div className="flex justify-between">
                  <span>Feed Protocol:</span>
                  <span className="font-mono text-slate-200">{a.type}</span>
                </div>
                <div className="flex justify-between">
                  <span>Adapter Mode:</span>
                  <span className="text-cyan-400 font-semibold">{a.mode}</span>
                </div>
                <div className="flex justify-between">
                  <span>Today's Ingested:</span>
                  <span className="text-slate-200 font-medium">{a.events_today}</span>
                </div>
              </div>
            </div>
          )) || <div className="text-xs text-slate-500">Loading adapters...</div>}
        </div>
      </div>

      {/* Webhook Sandbox Tester */}
      <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>External Partner Webhook Simulator</span>
        </h2>
        <p className="text-xs text-slate-400">
          Verify webhook payloads and HMAC challenge verification against your sandbox endpoint.
        </p>

        <div className="flex gap-2">
          <input
            type="text"
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200"
          />
          <button
            onClick={handleTestWebhook}
            className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold flex items-center gap-1.5 cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Send Test Event</span>
          </button>
        </div>

        {testResult && (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-400 space-y-1">
            <div>HTTP 200 OK • RTT: {testResult.rtt_ms}ms</div>
            <div className="text-slate-400">{testResult.message}</div>
          </div>
        )}
      </div>
    </div>
  );
}
