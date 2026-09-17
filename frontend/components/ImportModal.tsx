"use client";

import React, { useState } from "react";
import { X, Upload, FileSpreadsheet, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function ImportModal({ isOpen, onClose, onSuccess }: ImportModalProps) {
  const [carrier, setCarrier] = useState("Jio");
  const [coolingDays, setCoolingDays] = useState(60);
  const [csvText, setCsvText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: number; failed: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const sampleCsv = `phone,carrier,notes\n+919820011223,Jio,Corporate account closed\n+919811223344,Airtel,Prepaid 90 days expired\n+919830334455,Vi,Subscriber port out cancellation`;

  async function handleImport() {
    if (!csvText.trim()) {
      setError("Please paste CSV data or phone numbers.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const lines = csvText.trim().split("\n");
      const numbersToImport: Array<{ raw_phone: string; carrier: string; notes?: string }> = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line || (i === 0 && line.toLowerCase().includes("phone"))) continue;

        const parts = line.split(",").map((p) => p.trim());
        const phone = parts[0];
        const lineCarrier = parts[1] || carrier;
        const notes = parts[2] || "Batch CSV import";

        if (phone) {
          numbersToImport.push({ raw_phone: phone, carrier: lineCarrier, notes });
        }
      }

      if (numbersToImport.length === 0) {
        throw new Error("No valid phone number entries found in input.");
      }

      const res = await api.importNumbers(numbersToImport);
      setResult({ success: res.successful_count, failed: res.failed_count });
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (err: any) {
      setError(err.message || "Failed to process import.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
            <span>Import Decommissioned Numbers</span>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4 text-xs">
          {error && (
            <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800/60 text-rose-300 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>
                Successfully imported {result.success} numbers ({result.failed} failed).
              </span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Default Carrier</label>
              <select
                value={carrier}
                onChange={(e) => setCarrier(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="Jio">Jio Infocomm</option>
                <option value="Airtel">Bharti Airtel</option>
                <option value="Vi">Vodafone Idea (Vi)</option>
                <option value="BSNL">BSNL</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Cooling Window (Days)</label>
              <input
                type="number"
                value={coolingDays}
                onChange={(e) => setCoolingDays(Number(e.target.value))}
                min={30}
                max={180}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-slate-400 font-medium">Paste CSV / Numbers</label>
              <button
                type="button"
                onClick={() => setCsvText(sampleCsv)}
                className="text-[11px] text-cyan-400 hover:underline"
              >
                Load Sample Data
              </button>
            </div>
            <textarea
              rows={6}
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              placeholder="phone,carrier,notes&#10;+919820011223,Jio,Corporate disconnection&#10;+919811223344,Airtel,Prepaid expiry"
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-cyan-500"
            />
            <p className="mt-1 text-[10px] text-slate-500">
              Plain numbers will be hashed with HMAC-SHA256 and only masked forms will be visible.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleImport}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Upload className="w-3.5 h-3.5" />
                <span>Start Intake</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
