"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Key,
  Plus,
  RefreshCw,
  Trash2,
  Copy,
  Check,
  ShieldAlert,
  Calendar,
  Lock,
  ArrowLeft,
  Eye,
  AlertTriangle
} from "lucide-react";
import { api } from "@/lib/api";

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [scopes, setScopes] = useState("numbers:read,providers:write");
  const [expiresInDays, setExpiresInDays] = useState(90);
  const [newKeyResult, setNewKeyResult] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);
  const [creating, setCreating] = useState(false);

  const loadKeys = async () => {
    setLoading(true);
    try {
      const data = await api.listApiKeys();
      setKeys(data);
    } catch (err) {
      console.error("Failed to load API keys:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName) return;
    setCreating(true);
    try {
      const created = await api.createApiKey({
        name: keyName,
        scopes,
        expires_in_days: expiresInDays,
      });
      setNewKeyResult(created);
      setKeyName("");
      await loadKeys();
    } catch (err: any) {
      alert("Failed to create API key: " + err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleRotate = async (id: string) => {
    if (!confirm("Rotating this key will immediately invalidate the old token. Proceed?")) return;
    try {
      const rotated = await api.rotateApiKey(id);
      setNewKeyResult(rotated);
      await loadKeys();
    } catch (err: any) {
      alert("Failed to rotate key: " + err.message);
    }
  };

  const handleRevoke = async (id: string) => {
    if (!confirm("Are you sure you want to permanently revoke this API key?")) return;
    try {
      await api.revokeApiKey(id);
      await loadKeys();
    } catch (err: any) {
      alert("Failed to revoke key: " + err.message);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/settings"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Key className="w-5 h-5 text-indigo-400" />
              <span>Programmatic API Keys</span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Secure authentication tokens for B2B partner webhooks, automated lifecycle integrations, and HLR switches.
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            setNewKeyResult(null);
            setModalOpen(true);
          }}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Generate New Key</span>
        </button>
      </div>

      {/* Secret Key Alert (Shown Only Once) */}
      {newKeyResult && newKeyResult.raw_key && (
        <div className="p-5 rounded-xl border border-emerald-500/40 bg-emerald-950/20 backdrop-blur-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold">
              <Check className="w-4 h-4" />
              <span>API Key Created Successfully</span>
            </div>
            <span className="text-[11px] text-amber-400 font-medium">Shown only once</span>
          </div>

          <p className="text-xs text-slate-300">
            Copy and store this secret securely. It will never be displayed again.
          </p>

          <div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-950/90 border border-slate-800">
            <code className="text-xs font-mono text-emerald-300 flex-1 break-all">
              {newKeyResult.raw_key}
            </code>
            <button
              onClick={() => copyToClipboard(newKeyResult.raw_key)}
              className="px-3 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium flex items-center gap-1.5 transition flex-shrink-0"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied!" : "Copy"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Keys List */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Active API Keys</h2>
          <span className="text-xs text-slate-500">{keys.length} registered</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-medium">Key Label</th>
                <th className="px-4 py-3 font-medium">Prefix</th>
                <th className="px-4 py-3 font-medium">Scopes</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Expires</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                    Loading API keys...
                  </td>
                </tr>
              ) : keys.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                    No active API keys found. Generate one to enable programmatic access.
                  </td>
                </tr>
              ) : (
                keys.map((k) => (
                  <tr key={k.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-semibold text-white">{k.name}</td>
                    <td className="px-4 py-3 font-mono text-slate-400">{k.key_prefix}••••••••</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {k.scopes?.split(",").map((s: string) => (
                          <span
                            key={s}
                            className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 border border-slate-700"
                          >
                            {s.trim()}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {k.is_active ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950/60 text-rose-400 border border-rose-800">
                          Revoked
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {k.expires_at ? new Date(k.expires_at).toLocaleDateString() : "Never"}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      {k.is_active && (
                        <>
                          <button
                            onClick={() => handleRotate(k.id)}
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-medium transition"
                          >
                            Rotate
                          </button>
                          <button
                            onClick={() => handleRevoke(k.id)}
                            className="px-2 py-1 rounded bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800 text-[11px] font-medium transition"
                          >
                            Revoke
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Creation Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Key className="w-4 h-4 text-indigo-400" />
                <span>Create New API Key</span>
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Key Label / Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CI Webhook Pipeline"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Permissions & Scopes</label>
                <select
                  value={scopes}
                  onChange={(e) => setScopes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="numbers:read,providers:write">Standard Partner (Read numbers, unlinking status)</option>
                  <option value="numbers:read">Read Only (Lookups only)</option>
                  <option value="numbers:read,providers:write,webhooks:receive">Full Integration (Includes webhooks)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Validity Period</label>
                <select
                  value={expiresInDays}
                  onChange={(e) => setExpiresInDays(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value={30}>30 Days</option>
                  <option value={90}>90 Days (Recommended)</option>
                  <option value={180}>180 Days</option>
                  <option value={365}>1 Year</option>
                </select>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition disabled:opacity-50"
                >
                  {creating ? "Generating..." : "Create Secret Key"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
